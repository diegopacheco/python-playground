import threading
import uuid

from app.config import now_iso

STAGES = [
    "ORDERED",
    "BUILDING_IN_FACTORY",
    "SHIPPED",
    "ARRIVED_ON_SITE",
    "ASSEMBLED",
    "INSPECTED",
    "DELIVERED",
]

MODELS = {
    "aspen": {"name": "Aspen 2BR Modular", "bedrooms": 2, "sqft": 980, "price_usd": 189000},
    "birch": {"name": "Birch 3BR Ranch", "bedrooms": 3, "sqft": 1450, "price_usd": 264000},
    "cedar": {"name": "Cedar 4BR Two Story", "bedrooms": 4, "sqft": 2100, "price_usd": 348000},
    "dune": {"name": "Dune 1BR Tiny Home", "bedrooms": 1, "sqft": 420, "price_usd": 98000},
}


class HouseNotFound(Exception):
    pass


class InvalidTransition(Exception):
    pass


class HouseStore:
    def __init__(self):
        self._houses: dict[str, dict] = {}
        self._lock = threading.Lock()

    def create(self, model: str, lot: str, buyer_alias: str) -> dict:
        if model not in MODELS:
            raise ValueError(f"model must be one of {sorted(MODELS)}")
        if not lot or not buyer_alias:
            raise ValueError("lot and buyer_alias are required")
        house = {
            "id": str(uuid.uuid4()),
            "model": model,
            "model_details": MODELS[model],
            "lot": lot,
            "buyer_alias": buyer_alias,
            "status": STAGES[0],
            "updated_at": now_iso(),
        }
        with self._lock:
            self._houses[house["id"]] = house
            return dict(house)

    def advance(self, house_id: str) -> tuple[str, dict]:
        with self._lock:
            house = self._houses.get(house_id)
            if house is None:
                raise HouseNotFound(house_id)
            index = STAGES.index(house["status"])
            if index == len(STAGES) - 1:
                raise InvalidTransition(f"house {house_id} is already {house['status']}")
            previous = house["status"]
            house["status"] = STAGES[index + 1]
            house["updated_at"] = now_iso()
            return previous, dict(house)

    def all(self) -> list[dict]:
        with self._lock:
            return [dict(house) for house in self._houses.values()]
