import unittest

from game.config import BOSS_MAX_HP, TILE
from game.enemies import Walker
from game.layout import build_rows
from game.level import Level
from game.shot import buster_shot
from game.world import World
from tests.helpers import IDLE, RIGHT


def lane_world() -> World:
    rows = ["." * 60 for _ in range(17)] + ["#" * 60 for _ in range(3)]
    rows[16] = "P" + "." * 9 + "W.W" + "." * 37 + "A" + "." * 9
    return World(Level(rows))


class WorldTest(unittest.TestCase):
    def test_respawn_uses_the_reached_checkpoint(self) -> None:
        level = Level(build_rows())
        checkpoint = level.find("C")[0]
        world = World(level, checkpoint=1)
        self.assertEqual(world.player.body.x, checkpoint.col * TILE)

    def test_passing_a_checkpoint_saves_it(self) -> None:
        world = World(Level(build_rows()))
        world.player.body.x = 106 * TILE
        world.update(IDLE)
        self.assertEqual(world.checkpoint, 1)

    def test_entering_the_arena_starts_the_fight_and_locks_the_player_in(self) -> None:
        world = World(Level(build_rows()), checkpoint=2)
        for _ in range(120):
            world.update(RIGHT)
        self.assertTrue(world.boss_fight)
        self.assertEqual(world.level.tile(world.arena_col, 16), "#")
        self.assertGreaterEqual(world.cam_x, world.arena_col * TILE)

    def test_defeating_the_boss_wins_the_game(self) -> None:
        world = World(Level(build_rows()), checkpoint=2)
        assert world.boss is not None
        world.boss.hit(BOSS_MAX_HP)
        world.update(IDLE)
        self.assertTrue(world.won)

    def test_full_charge_shot_pierces_enemies_it_destroys(self) -> None:
        world = lane_world()
        b = world.player.body
        world.shots.append(buster_shot(b.x + b.w, b.y + 8, 1, 3))
        for _ in range(30):
            world.update(IDLE)
        self.assertEqual(world.enemies, [])

    def test_medium_shot_stops_at_the_first_enemy(self) -> None:
        world = lane_world()
        b = world.player.body
        world.shots.append(buster_shot(b.x + b.w, b.y + 8, 1, 2))
        for _ in range(30):
            world.update(IDLE)
        hp = sorted(e.hp for e in world.enemies if isinstance(e, Walker))
        self.assertEqual(hp, [1, 3])

    def test_touching_an_enemy_costs_contact_damage(self) -> None:
        world = lane_world()
        enemy = world.enemies[0]
        world.player.body.x = enemy.body.x
        world.player.body.y = enemy.body.y - 6
        before = world.player.hp
        world.update(IDLE)
        self.assertEqual(world.player.hp, before - enemy.contact_damage)


if __name__ == "__main__":
    unittest.main()
