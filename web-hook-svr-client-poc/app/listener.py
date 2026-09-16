from app.config import required
from app.event_store import EventStore
from app.http_json import JsonHandler, serve
from app.subscriber import RelaySubscriber


def make_handler(store: EventStore, subscriber: RelaySubscriber) -> type[JsonHandler]:
    class Handler(JsonHandler):
        def do_GET(self):
            if self.path == "/health":
                return self.send_json(200, {"status": "UP", "relay_connected": subscriber.connected.is_set()})
            if self.path == "/api/events":
                return self.send_json(200, store.all())
            self.send_json(404, {"error": "not found"})

    return Handler


def main():
    store = EventStore(required("LISTENER_DB"))
    subscriber = RelaySubscriber(required("RELAY_URL"), required("WEBHOOK_SECRET"), store)
    subscriber.start()
    serve(int(required("LISTENER_PORT")), make_handler(store, subscriber))


if __name__ == "__main__":
    main()
