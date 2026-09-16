import unittest
import uuid

from app.correlation import correlation_id_from


class CorrelationTest(unittest.TestCase):
    def test_caller_correlation_id_is_kept_so_it_can_trace_its_own_request(self) -> None:
        self.assertEqual("order-2026.09_16-A", correlation_id_from("order-2026.09_16-A"))

    def test_missing_correlation_id_gets_a_new_uuid(self) -> None:
        self.assertEqual(4, uuid.UUID(correlation_id_from(None)).version)

    def test_unsafe_correlation_id_is_replaced_so_it_cannot_inject_headers_or_logs(self) -> None:
        for unsafe in ("", "a b", "x\r\nSet-Cookie: y", "id=<script>", "a" * 65):
            generated = correlation_id_from(unsafe)
            self.assertNotEqual(unsafe, generated)
            self.assertEqual(4, uuid.UUID(generated).version)


if __name__ == "__main__":
    unittest.main()
