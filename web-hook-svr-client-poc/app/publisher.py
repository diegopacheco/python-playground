import time
import urllib.request
import uuid

from app.config import now_iso
from app.signing import canonical, sign


class WebhookPublisher:
    def __init__(self, target_url: str, secret: str):
        self.target_url = target_url
        self.secret = secret

    def publish(self, event_type: str, data: dict) -> int:
        payload = {"id": str(uuid.uuid4()), "type": event_type, "created_at": now_iso(), "data": data}
        timestamp = str(int(time.time()))
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "prebuilt-houses-webhooks/1.0",
            "X-Webhook-Event": event_type,
            "X-Webhook-Timestamp": timestamp,
            "X-Webhook-Signature": sign(self.secret, timestamp, payload),
        }
        request = urllib.request.Request(
            self.target_url, data=canonical(payload).encode(), headers=headers, method="POST"
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status
