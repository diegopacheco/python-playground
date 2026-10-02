import unittest

from game.config import TILE
from game.level import Level
from game.physics import Body, apply_gravity, move
from tests.helpers import flat_level


class PhysicsTest(unittest.TestCase):
    def test_falling_body_rests_exactly_on_ground_top(self) -> None:
        level = flat_level()
        body = Body(16, 0, 10, 16)
        for _ in range(120):
            apply_gravity(body)
            move(body, level)
        self.assertTrue(body.on_ground)
        self.assertEqual(body.y + body.h, 17 * TILE)

    def test_running_into_a_wall_stops_flush_and_reports_wall_side(self) -> None:
        rows = ["." * 10 + "#" + "." * 9 for _ in range(20)]
        level = Level(rows)
        body = Body(60, 40, 10, 16, vx=3.0)
        for _ in range(10):
            body.vx = 3.0
            move(body, level)
        self.assertEqual(body.x + body.w, 10 * TILE)
        self.assertEqual(body.wall, 1)

    def test_head_bump_cancels_upward_speed(self) -> None:
        rows = ["#" * 20] + ["." * 20 for _ in range(19)]
        level = Level(rows)
        body = Body(40, 20, 10, 16, vy=-8.0)
        for _ in range(3):
            move(body, level)
        self.assertEqual(body.y, TILE)
        self.assertEqual(body.vy, 0.0)


if __name__ == "__main__":
    unittest.main()
