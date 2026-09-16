import time
import urllib.parse
import urllib.request
import uuid

from app.config import now_iso
from app.correlation import HEADER
from app.signing import canonical, sign


class WebhookPublisher:
    def __init__(self, target_url: str, secret: str) -> None:
        self.target_url = target_url
        self.secret = secret
        self.deliveries: list[dict] = []

    def publish(self, event_type: str, data: dict, correlation_id: str) -> int:
        payload = {
            "id": str(uuid.uuid4()),
            "correlation_id": correlation_id,
            "type": event_type,
            "created_at": now_iso(),
            "data": data,
        }
        body = canonical(payload).encode()
        timestamp = str(int(time.time()))
        headers = {
            "Host": urllib.parse.urlsplit(self.target_url).netloc,
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
            "User-Agent": "prebuilt-houses-webhooks/1.0",
            "Accept-Encoding": "identity",
            "Connection": "close",
            HEADER: correlation_id,
            "X-Webhook-Event": event_type,
            "X-Webhook-Timestamp": timestamp,
            "X-Webhook-Signature": sign(self.secret, timestamp, payload),
        }
        request = urllib.request.Request(self.target_url, data=body, headers=headers, method="POST")
        sent_at = now_iso()
        with urllib.request.urlopen(request, timeout=10) as response:
            self.deliveries.append(
                {
                    "id": payload["id"],
                    "correlation_id": correlation_id,
                    "sent_at": sent_at,
                    "relay_status": response.status,
                    "headers": headers,
                }
            )
            return response.status
