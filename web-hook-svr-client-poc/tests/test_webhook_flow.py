import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from app.houses import HouseStore
from app.publisher import WebhookPublisher
from app.subscriber import to_event
from app.webhook_server import make_handler

SECRET = "synthetic-secret"


class FakeRelay(BaseHTTPRequestHandler):
    received: list[dict] = []

    def do_POST(self) -> None:
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        message = {name.lower(): value for name, value in self.headers.items()}
        FakeRelay.received.append({**message, "client-ip": "198.51.100.1", "body": body})
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args: object) -> None:
        pass


def start(handler: type[BaseHTTPRequestHandler]) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


class WebhookFlowTest(unittest.TestCase):
    def setUp(self) -> None:
        FakeRelay.received = []
        self.relay = start(FakeRelay)
        relay_url = f"http://127.0.0.1:{self.relay.server_port}/channel"
        self.publisher = WebhookPublisher(relay_url, SECRET)
        self.server = start(make_handler(HouseStore(), self.publisher))
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        for server in (self.server, self.relay):
            server.shutdown()
            server.server_close()

    def post(self, path: str, body: dict | None = None) -> tuple[int, dict]:
        request = urllib.request.Request(
            self.base + path, data=json.dumps(body or {}).encode(), headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(request) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            with error:
                return error.code, json.load(error)

    def test_every_house_change_reaches_the_listener_as_a_valid_signed_event(self) -> None:
        status, created = self.post("/api/houses", {"model": "cedar", "lot": "Lot C-03", "buyer_alias": "buyer-0003"})
        self.assertEqual(201, status)
        house_id = created["house"]["id"]
        for _ in range(6):
            self.assertEqual(200, self.post(f"/api/houses/{house_id}/advance")[0])

        events = [to_event(message, SECRET) for message in FakeRelay.received]
        self.assertEqual(7, len(events))
        self.assertTrue(all(event["signature_valid"] for event in events))
        self.assertEqual("house.ordered", events[0]["type"])
        self.assertEqual(house_id, events[0]["payload"]["data"]["house"]["id"])
        self.assertTrue(all(event["payload"]["data"]["house"]["id"] == house_id for event in events))
        self.assertEqual("house.delivered", events[-1]["type"])
        self.assertEqual("DELIVERED", events[-1]["payload"]["data"]["house"]["status"])

    def test_out_headers_shown_in_the_admin_are_exactly_the_headers_on_the_wire(self) -> None:
        self.post("/api/houses", {"model": "birch", "lot": "Lot B-02", "buyer_alias": "buyer-0002"})
        with urllib.request.urlopen(self.base + "/api/deliveries") as response:
            deliveries = json.load(response)
        wire = {name: value for name, value in FakeRelay.received[0].items() if name not in ("client-ip", "body")}
        recorded = {name.lower(): value for name, value in deliveries[0]["headers"].items()}
        self.assertEqual(wire, recorded)
        self.assertEqual(FakeRelay.received[0]["body"]["id"], deliveries[0]["id"])
        self.assertEqual(200, deliveries[0]["relay_status"])

    def test_failed_delivery_is_not_recorded_as_sent(self) -> None:
        self.relay.shutdown()
        self.relay.server_close()
        self.post("/api/houses", {"model": "aspen", "lot": "Lot A-01", "buyer_alias": "buyer-0001"})
        self.relay = start(FakeRelay)
        self.assertEqual([], self.publisher.deliveries)

    def test_advancing_a_delivered_house_sends_no_webhook(self) -> None:
        _, created = self.post("/api/houses", {"model": "dune", "lot": "Lot D-04", "buyer_alias": "buyer-0004"})
        for _ in range(6):
            self.post(f"/api/houses/{created['house']['id']}/advance")
        status, _ = self.post(f"/api/houses/{created['house']['id']}/advance")
        self.assertEqual(409, status)
        self.assertEqual(7, len(FakeRelay.received))

    def test_invalid_order_is_rejected_without_sending_a_webhook(self) -> None:
        status, _ = self.post("/api/houses", {"model": "castle", "lot": "Lot Z-99", "buyer_alias": "buyer-0099"})
        self.assertEqual(400, status)
        self.assertEqual([], FakeRelay.received)

    def test_relay_down_is_reported_as_502_instead_of_silent_success(self) -> None:
        self.relay.shutdown()
        self.relay.server_close()
        status, body = self.post("/api/houses", {"model": "aspen", "lot": "Lot A-01", "buyer_alias": "buyer-0001"})
        self.relay = start(FakeRelay)
        self.assertEqual(502, status)
        self.assertIn("webhook delivery failed", body["error"])


if __name__ == "__main__":
    unittest.main()
