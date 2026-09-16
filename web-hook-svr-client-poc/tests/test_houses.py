import unittest

from app.houses import STAGES, HouseNotFound, HouseStore, InvalidTransition
from app.webhook_server import event_type_for


class HouseStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.store = HouseStore()

    def test_new_order_starts_as_ordered_with_catalog_details(self) -> None:
        house = self.store.create("aspen", "Lot A-01", "buyer-0001")
        self.assertEqual("ORDERED", house["status"])
        self.assertEqual(189000, house["model_details"]["price_usd"])

    def test_house_moves_through_every_construction_stage_in_order(self) -> None:
        house = self.store.create("birch", "Lot B-02", "buyer-0002")
        seen = []
        for _ in STAGES[1:]:
            previous, house = self.store.advance(house["id"])
            seen.append((previous, house["status"]))
        self.assertEqual(list(zip(STAGES, STAGES[1:])), seen)

    def test_a_delivered_house_cannot_move_again(self) -> None:
        house = self.store.create("dune", "Lot D-04", "buyer-0004")
        for _ in STAGES[1:]:
            self.store.advance(house["id"])
        with self.assertRaises(InvalidTransition):
            self.store.advance(house["id"])

    def test_unknown_model_is_rejected_so_no_webhook_carries_an_unpriced_house(self) -> None:
        with self.assertRaises(ValueError):
            self.store.create("castle", "Lot Z-99", "buyer-0099")

    def test_lot_and_buyer_alias_are_required(self) -> None:
        with self.assertRaises(ValueError):
            self.store.create("aspen", "", "buyer-0001")

    def test_unknown_house_is_not_found(self) -> None:
        with self.assertRaises(HouseNotFound):
            self.store.advance("00000000-0000-0000-0000-000000000000")

    def test_only_the_final_stage_emits_house_delivered(self) -> None:
        self.assertEqual("house.delivered", event_type_for("DELIVERED"))
        self.assertEqual("house.status_changed", event_type_for("INSPECTED"))


if __name__ == "__main__":
    unittest.main()
