import unittest

from game.config import HEIGHT, TILE
from game.layout import build_rows
from game.level import Level


class LevelLayoutTest(unittest.TestCase):
    def setUp(self) -> None:
        self.level = Level(build_rows())

    def test_level_fills_the_screen_height_so_there_is_no_vertical_scroll(self) -> None:
        self.assertEqual(self.level.rows * TILE, HEIGHT)

    def test_level_has_one_start_one_boss_and_one_arena_gate(self) -> None:
        for kind in "PBA":
            self.assertEqual(len(self.level.find(kind)), 1, kind)

    def test_ground_enemies_and_checkpoints_stand_on_solid_tiles(self) -> None:
        for spawn in self.level.spawns:
            if spawn.kind in "PCWTB":
                below = self.level.tile(spawn.col, spawn.row + 1)
                self.assertEqual(below, "#", f"{spawn} would fall")

    def test_markers_are_cleared_from_the_tile_grid(self) -> None:
        for spawn in self.level.spawns:
            self.assertEqual(self.level.tile(spawn.col, spawn.row), ".")

    def test_boss_arena_is_one_screen_wide_at_the_end(self) -> None:
        gate = self.level.find("A")[0]
        self.assertEqual((self.level.cols - gate.col) * TILE, 256)

    def test_outside_horizontal_bounds_is_solid_and_below_is_open(self) -> None:
        self.assertEqual(self.level.tile(-1, 5), "#")
        self.assertEqual(self.level.tile(self.level.cols, 5), "#")
        self.assertEqual(self.level.tile(5, self.level.rows), ".")

    def test_ragged_rows_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Level(["...", ".."])


if __name__ == "__main__":
    unittest.main()
