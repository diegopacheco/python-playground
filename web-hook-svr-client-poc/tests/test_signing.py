import json
import unittest

from app.signing import sign, verify

SECRET = "synthetic-secret"
PAYLOAD = {"id": "evt-1", "type": "house.ordered", "data": {"lot": "Lot A-01", "price_usd": 189000}}


class SigningTest(unittest.TestCase):
    def test_signature_from_the_server_is_accepted(self) -> None:
        signature = sign(SECRET, "1700000000", PAYLOAD)
        self.assertTrue(verify(SECRET, "1700000000", PAYLOAD, signature))

    def test_relay_reserializing_the_body_with_other_key_order_still_verifies(self) -> None:
        reordered = json.loads(json.dumps({"data": PAYLOAD["data"], "type": PAYLOAD["type"], "id": PAYLOAD["id"]}))
        self.assertTrue(verify(SECRET, "1700000000", reordered, sign(SECRET, "1700000000", PAYLOAD)))

    def test_anyone_posting_to_the_public_relay_without_the_secret_is_rejected(self) -> None:
        forged = sign("guessed-secret", "1700000000", PAYLOAD)
        self.assertFalse(verify(SECRET, "1700000000", PAYLOAD, forged))

    def test_tampered_payload_is_rejected(self) -> None:
        signature = sign(SECRET, "1700000000", PAYLOAD)
        tampered = {**PAYLOAD, "type": "house.delivered"}
        self.assertFalse(verify(SECRET, "1700000000", tampered, signature))

    def test_replaying_a_signature_with_another_timestamp_is_rejected(self) -> None:
        signature = sign(SECRET, "1700000000", PAYLOAD)
        self.assertFalse(verify(SECRET, "1700009999", PAYLOAD, signature))

    def test_missing_headers_are_rejected(self) -> None:
        self.assertFalse(verify(SECRET, None, PAYLOAD, None))


if __name__ == "__main__":
    unittest.main()
