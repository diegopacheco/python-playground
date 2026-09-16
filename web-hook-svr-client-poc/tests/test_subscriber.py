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
        "host": "smee.io",
        "client-ip": "203.0.113.7:5555",
        "x-forwarded-for": "203.0.113.7",
        "x-client-port": "5555",
        "x-original-url": "/synthetic-channel",
        "x-real-address": "2001:db8::7",
        "user-agent": "prebuilt-houses-webhooks/1.0",
        "x-webhook-event": payload["type"],
        "x-webhook-timestamp": "1700000000",
        "x-webhook-signature": sign(secret, "1700000000", payload),
        "body": payload,
        "query": {},
        "timestamp": 1700000000123,
    }


def sse(*frames: str) -> list[bytes]:
    return [line.encode() + b"\n" for frame in frames for line in frame.split("\n")] + [b"\n"]


class SubscriberTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.store = EventStore(os.path.join(self.directory.name, "events.db"))
        self.subscriber = RelaySubscriber("https://relay.invalid/channel", SECRET, self.store)
        self.payload = {"id": "evt-1", "type": "house.ordered", "data": {"house": {"lot": "Lot A-01"}}}

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_sender_ip_headers_added_by_the_relay_are_never_stored(self) -> None:
        event = to_event(relay_message(self.payload), SECRET)
        self.assertNotIn("203.0.113.7", json.dumps(event))

    def test_ip_port_and_channel_url_are_redacted_even_under_unknown_header_names(self) -> None:
        stored = json.dumps(to_event(relay_message(self.payload), SECRET)["headers"])
        for private in ("5555", "synthetic-channel", "2001:db8::7"):
            self.assertNotIn(private, stored)

    def test_every_relay_header_name_is_kept_so_the_admin_sees_what_arrived(self) -> None:
        headers = to_event(relay_message(self.payload), SECRET)["headers"]
        expected = set(relay_message(self.payload)) - {"body", "query", "timestamp"}
        self.assertEqual(expected, set(headers))
        self.assertEqual("prebuilt-houses-webhooks/1.0", headers["user-agent"])
        self.assertEqual("[redacted]", headers["client-ip"])

    def test_relay_timestamp_becomes_the_relay_step_of_the_flow(self) -> None:
        event = to_event(relay_message(self.payload), SECRET)
        self.assertEqual("2023-11-14T22:13:20.123+00:00", event["relayed_at"])

    def test_signed_event_from_the_server_is_valid(self) -> None:
        self.assertTrue(to_event(relay_message(self.payload), SECRET)["signature_valid"])

    def test_event_signed_with_another_secret_is_stored_as_rejected(self) -> None:
        self.assertFalse(to_event(relay_message(self.payload, "other"), SECRET)["signature_valid"])

    def test_relay_messages_without_a_json_body_are_ignored(self) -> None:
        self.assertIsNone(to_event({"body": "plain text"}, SECRET))

    def test_parse_sse_splits_named_and_default_events(self) -> None:
        frames = list(parse_sse(sse("id: 0\nevent: ready\ndata: {}\n", 'id: 1\ndata: {"a": 1}')))
        self.assertEqual([("ready", "{}"), ("message", '{"a": 1}')], frames)

    def test_ready_event_marks_the_listener_connected(self) -> None:
        self.subscriber.consume(sse("event: ready\ndata: {}"))
        self.assertTrue(self.subscriber.connected.is_set())

    def test_stored_event_keeps_the_correlation_id_from_the_signed_payload(self) -> None:
        payload = {**self.payload, "correlation_id": "journey-9"}
        self.subscriber.consume(sse("data: " + json.dumps(relay_message(payload)) + "\n"))
        self.assertEqual("journey-9", self.store.all()[0]["correlation_id"])

    def test_same_webhook_delivered_twice_is_stored_once(self) -> None:
        frame = "data: " + json.dumps(relay_message(self.payload)) + "\n"
        self.subscriber.consume(sse(frame, frame))
        self.assertEqual(1, len(self.store.all()))
        self.assertEqual("[redacted]", self.store.all()[0]["headers"]["x-forwarded-for"])


if __name__ == "__main__":
    unittest.main()
