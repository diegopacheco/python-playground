import unittest

from game.config import DASH_SPEED, FULL_CHARGE, HALF_CHARGE, PLAYER_MAX_HP, RUN_SPEED, TILE
from game.controls import Controls
from game.layout import build_rows
from game.level import Level
from game.player import Player
from game.shot import Shot
from tests.helpers import IDLE, RIGHT, flat_level


def settle(player: Player, level: Level) -> None:
    for _ in range(60):
        player.update(IDLE, level)


def highest_footing(player: Player, level: Level, frames: int, wall_jumps: bool) -> float:
    pressed_last = False
    best = player.body.y + player.body.h
    for _ in range(frames):
        b = player.body
        can_jump = b.on_ground or (wall_jumps and b.wall == 1)
        jump = can_jump and not pressed_last
        player.update(Controls(right=True, jump=jump, jump_held=True), level)
        pressed_last = jump
        if b.on_ground:
            best = min(best, b.y + b.h)
    return best


def hold_shoot(player: Player, level: Level, frames: int) -> list[Shot]:
    shots = player.update(Controls(shoot=True, shoot_held=True), level)
    for _ in range(frames - 1):
        shots += player.update(Controls(shoot_held=True), level)
    return shots + player.update(IDLE, level)


class MovementTest(unittest.TestCase):
    def test_tall_wall_needs_wall_jumps_to_climb(self) -> None:
        level = Level(build_rows())
        wall_top = 7 * TILE
        plain = Player(80 * TILE, 15 * TILE)
        settle(plain, level)
        self.assertGreater(highest_footing(plain, level, 300, wall_jumps=False), wall_top)

        climber = Player(80 * TILE, 15 * TILE)
        settle(climber, level)
        self.assertEqual(highest_footing(climber, level, 300, wall_jumps=True), wall_top)

    def test_first_spike_pit_can_be_cleared_with_a_running_jump(self) -> None:
        level = Level(build_rows())
        player = Player(30 * TILE, 15 * TILE)
        settle(player, level)
        jumped = False
        for _ in range(200):
            edge = not jumped and player.body.x + player.body.w >= 42 * TILE - 2
            jumped = jumped or edge
            player.update(Controls(right=True, jump=edge, jump_held=True), level)
        self.assertTrue(player.alive)
        self.assertGreater(player.body.x, 47 * TILE)

    def test_falling_into_spikes_kills_instantly(self) -> None:
        level = Level(build_rows())
        player = Player(43 * TILE, 10 * TILE)
        for _ in range(60):
            player.update(IDLE, level)
        self.assertFalse(player.alive)

    def test_dash_is_faster_than_running_and_dash_jump_keeps_the_speed(self) -> None:
        level = flat_level(200)
        player = Player(16, 15 * TILE)
        settle(player, level)
        player.update(Controls(right=True, dash=True, dash_held=True), level)
        self.assertEqual(player.body.vx, DASH_SPEED)
        player.update(Controls(right=True, jump=True, jump_held=True, dash_held=True), level)
        for _ in range(10):
            player.update(Controls(right=True, jump_held=True), level)
        self.assertFalse(player.body.on_ground)
        self.assertEqual(player.body.vx, DASH_SPEED)
        self.assertGreater(DASH_SPEED, RUN_SPEED)

    def test_releasing_jump_early_gives_a_shorter_jump(self) -> None:
        level = flat_level()
        def peak(hold: int) -> float:
            player = Player(16, 15 * TILE)
            settle(player, level)
            top = player.body.y
            player.update(Controls(jump=True, jump_held=True), level)
            for i in range(60):
                player.update(Controls(jump_held=i < hold), level)
                top = min(top, player.body.y)
            return top
        self.assertGreater(peak(2), peak(60))


class BusterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.level = flat_level(200)
        self.player = Player(16, 15 * TILE)
        settle(self.player, self.level)

    def test_tap_fires_one_weak_shot(self) -> None:
        shots = hold_shoot(self.player, self.level, 1)
        self.assertEqual([s.damage for s in shots], [1])

    def test_half_charge_adds_a_medium_shot_on_release(self) -> None:
        shots = hold_shoot(self.player, self.level, HALF_CHARGE)
        self.assertEqual([s.damage for s in shots], [1, 2])

    def test_full_charge_adds_the_strongest_shot_on_release(self) -> None:
        shots = hold_shoot(self.player, self.level, FULL_CHARGE)
        self.assertEqual([s.damage for s in shots], [1, 4])
        self.assertEqual(self.player.charge, 0)

    def test_shots_travel_the_way_the_player_faces(self) -> None:
        self.player.update(Controls(left=True), self.level)
        shots = hold_shoot(self.player, self.level, 1)
        self.assertLess(shots[0].body.vx, 0)


class DamageTest(unittest.TestCase):
    def test_invulnerability_blocks_damage_right_after_a_hit(self) -> None:
        player = Player(16, 15 * TILE)
        player.hurt(3, 100)
        player.hurt(3, 100)
        self.assertEqual(player.hp, PLAYER_MAX_HP - 3)

    def test_knockback_pushes_away_from_the_attacker(self) -> None:
        player = Player(50, 15 * TILE)
        player.hurt(1, 100)
        self.assertLess(player.body.vx, 0)


if __name__ == "__main__":
    unittest.main()
