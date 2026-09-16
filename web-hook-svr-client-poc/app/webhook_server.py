import re
import urllib.error

from app.config import required
from app.houses import MODELS, STAGES, HouseNotFound, HouseStore, InvalidTransition
from app.http_json import JsonHandler, serve
from app.publisher import WebhookPublisher

ADVANCE_PATH = re.compile(r"/api/houses/([0-9a-f-]{36})/advance")


def event_type_for(status: str) -> str:
    return "house.delivered" if status == STAGES[-1] else "house.status_changed"


def make_handler(store: HouseStore, publisher: WebhookPublisher) -> type[JsonHandler]:
    class Handler(JsonHandler):
        def do_GET(self) -> None:
            if self.path == "/health":
                return self.send_json(200, {"status": "UP"})
            if self.path == "/api/models":
                return self.send_json(200, MODELS)
            if self.path == "/api/houses":
                return self.send_json(200, store.all())
            if self.path == "/api/deliveries":
                return self.send_json(200, publisher.deliveries)
            self.send_json(404, {"error": "not found"})

        def do_POST(self) -> None:
            if self.path == "/api/houses":
                return self.create_house()
            match = ADVANCE_PATH.fullmatch(self.path)
            if match:
                return self.advance_house(match.group(1))
            self.send_json(404, {"error": "not found"})

        def create_house(self) -> None:
            body = self.read_json()
            try:
                house = store.create(body.get("model", ""), body.get("lot", ""), body.get("buyer_alias", ""))
            except ValueError as error:
                return self.send_json(400, {"error": str(error)})
            data = {"house": house}
            self.deliver(201, "house.ordered", data, data)

        def advance_house(self, house_id: str) -> None:
            try:
                previous, house = store.advance(house_id)
            except HouseNotFound:
                return self.send_json(404, {"error": f"house {house_id} not found"})
            except InvalidTransition as error:
                return self.send_json(409, {"error": str(error)})
            data = {"house": house, "previous_status": previous}
            self.deliver(200, event_type_for(house["status"]), data, data)

        def deliver(self, status: int, event_type: str, data: dict, response: dict) -> None:
            try:
                webhook_status = publisher.publish(event_type, data)
            except (urllib.error.URLError, TimeoutError) as error:
                return self.send_json(502, {**response, "error": f"webhook delivery failed: {error}"})
            self.send_json(status, {**response, "event": event_type, "webhook_status": webhook_status})

    return Handler


def main() -> None:
    publisher = WebhookPublisher(required("RELAY_URL"), required("WEBHOOK_SECRET"))
    serve(int(required("WEBHOOK_SERVER_PORT")), make_handler(HouseStore(), publisher))


if __name__ == "__main__":
    main()
