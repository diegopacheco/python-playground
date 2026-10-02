from enum import Enum, auto

import pyxel

from game.config import BOSS_MAX_HP
from game.enemies import Enemy
from game.level import Level
from game.physics import Body, apply_gravity, move
from game.player import Player
from game.shot import Shot, enemy_shot


class Move(Enum):
    IDLE = auto()
    JUMP = auto()
    SHOOT = auto()
    DASH = auto()


PATTERN = (Move.JUMP, Move.SHOOT, Move.DASH, Move.SHOOT)


class Boss(Enemy):
    contact_damage = 3
    is_boss = True

    def __init__(self, x: float, y: float) -> None:
        super().__init__(Body(x, y, 18, 24), hp=BOSS_MAX_HP)
        self.active = False
        self.move = Move.IDLE
        self.move_timer = 0
        self.pattern_index = 0
        self.facing = -1

    @property
    def enraged(self) -> bool:
        return self.hp <= BOSS_MAX_HP // 2

    def act(self, player: Player, level: Level) -> list[Shot]:
        b = self.body
        apply_gravity(b)
        if not self.active:
            move(b, level)
            return []
        self.move_timer += 1
        shots: list[Shot] = []
        match self.move:
            case Move.IDLE:
                b.vx = 0.0
                self.facing = 1 if player.body.cx > b.cx else -1
                if self.move_timer >= (20 if self.enraged else 45):
                    self._next(player)
            case Move.JUMP:
                if b.on_ground and self.move_timer > 2:
                    self._idle()
            case Move.SHOOT:
                if self.move_timer in (10, 25, 40):
                    shots.extend(self._spread())
                if self.move_timer >= 50:
                    self._idle()
            case Move.DASH:
                b.vx = self.facing * (3.5 if self.enraged else 2.8)
                if b.wall == self.facing:
                    self._idle()
        move(b, level)
        return shots

    def _next(self, player: Player) -> None:
        b = self.body
        self.move = PATTERN[self.pattern_index % len(PATTERN)]
        self.pattern_index += 1
        self.move_timer = 0
        if self.move is Move.JUMP:
            b.vy = -5.5
            b.vx = max(-2.0, min(2.0, (player.body.cx - b.cx) / 40))

    def _idle(self) -> None:
        self.move = Move.IDLE
        self.move_timer = 0
        self.body.vx = 0.0

    def _spread(self) -> list[Shot]:
        b = self.body
        muzzle = b.x + b.w + 2 if self.facing > 0 else b.x - 2
        angles = (-0.6, 0.0, 0.6) if self.enraged else (-0.3, 0.3)
        return [enemy_shot(muzzle, b.y + 10, self.facing * 2.5, vy) for vy in angles]

    def render(self, x: int, y: int) -> None:
        f = self.facing

        def part(px: int, py: int, pw: int, ph: int, col: int) -> None:
            left = x + px if f > 0 else x + 18 - px - pw
            pyxel.rect(left, y + py, pw, ph, col)

        armor = 8 if self.enraged and self.timer % 8 < 4 else 2
        part(3, 0, 12, 8, armor)
        part(6, -3, 2, 4, 10)
        part(10, -3, 2, 4, 10)
        part(9, 3, 6, 4, 0)
        part(11, 4, 3, 1, 8)
        part(1, 8, 16, 9, armor)
        part(4, 9, 10, 4, 14)
        part(13, 10, 7, 4, 13)
        part(2, 17, 5, 7, 1)
        part(11, 17, 5, 7, 1)
        part(1, 22, 7, 2, 13)
        part(10, 22, 7, 2, 13)
        if self.move is Move.DASH:
            part(-4, 12, 4, 2, 10)
