import json
import os
import tempfile
import unittest

from app.event_store import EventStore
from app.signing import sign
from app.subscriber import RelaySubscriber, parse_sse, to_event

SECRET = "synthetic-secret"


def relay_message(payload: dict, secret: str = SECRET) -> dict:
    return {
        "client-ip": "203.0.113.7:5555",
        "x-forwarded-for": "203.0.113.7",
        "user-agent": "prebuilt-houses-webhooks/1.0",
        "x-webhook-event": payload["type"],
        "x-webhook-timestamp": "1700000000",
        "x-webhook-signature": sign(secret, "1700000000", payload),
        "body": payload,
    }


def sse(*frames: str) -> list[bytes]:
    return [line.encode() + b"\n" for frame in frames for line in frame.split("\n")] + [b"\n"]


class SubscriberTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.store = EventStore(os.path.join(self.directory.name, "events.db"))
        self.subscriber = RelaySubscriber("https://relay.invalid/channel", SECRET, self.store)
        self.payload = {"id": "evt-1", "type": "house.ordered", "data": {"house": {"lot": "Lot A-01"}}}

    def tearDown(self):
        self.directory.cleanup()

    def test_sender_ip_headers_added_by_the_relay_are_never_stored(self):
        event = to_event(relay_message(self.payload), SECRET)
        self.assertNotIn("203.0.113.7", json.dumps(event))

    def test_signed_event_from_the_server_is_valid(self):
        self.assertTrue(to_event(relay_message(self.payload), SECRET)["signature_valid"])

    def test_event_signed_with_another_secret_is_stored_as_rejected(self):
        self.assertFalse(to_event(relay_message(self.payload, "other"), SECRET)["signature_valid"])

    def test_relay_messages_without_a_json_body_are_ignored(self):
        self.assertIsNone(to_event({"body": "plain text"}, SECRET))

    def test_parse_sse_splits_named_and_default_events(self):
        frames = list(parse_sse(sse("id: 0\nevent: ready\ndata: {}\n", 'id: 1\ndata: {"a": 1}')))
        self.assertEqual([("ready", "{}"), ("message", '{"a": 1}')], frames)

    def test_ready_event_marks_the_listener_connected(self):
        self.subscriber.consume(sse("event: ready\ndata: {}"))
        self.assertTrue(self.subscriber.connected.is_set())

    def test_same_webhook_delivered_twice_is_stored_once(self):
        frame = "data: " + json.dumps(relay_message(self.payload)) + "\n"
        self.subscriber.consume(sse(frame, frame))
        self.assertEqual(1, len(self.store.all()))


if __name__ == "__main__":
    unittest.main()
