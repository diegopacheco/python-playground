import math
from abc import ABC, abstractmethod

import pyxel

from game.config import TILE
from game.level import Level
from game.physics import Body, apply_gravity, move
from game.player import Player
from game.shot import Shot, enemy_shot


class Enemy(ABC):
    contact_damage = 2
    is_boss = False

    def __init__(self, body: Body, hp: int) -> None:
        self.body = body
        self.hp = hp
        self.flash = 0
        self.timer = 0

    @property
    def alive(self) -> bool:
        return self.hp > 0

    def hit(self, damage: int) -> None:
        self.hp = max(0, self.hp - damage)
        self.flash = 4

    def update(self, player: Player, level: Level) -> list[Shot]:
        self.flash = max(0, self.flash - 1)
        self.timer += 1
        return self.act(player, level)

    def draw(self) -> None:
        if self.flash > 0:
            for col in range(16):
                pyxel.pal(col, 7)
        self.render(round(self.body.x), round(self.body.y))
        pyxel.pal()

    @abstractmethod
    def act(self, player: Player, level: Level) -> list[Shot]: ...

    @abstractmethod
    def render(self, x: int, y: int) -> None: ...


class Walker(Enemy):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(Body(x, y, 12, 10, vx=-0.5), hp=3)

    def act(self, player: Player, level: Level) -> list[Shot]:
        b = self.body
        speed = b.vx
        apply_gravity(b)
        move(b, level)
        heading = 1 if speed > 0 else -1
        ahead = b.x + b.w + 1 if heading > 0 else b.x - 1
        no_floor = b.on_ground and not level.hits(ahead, b.y + b.h, 1, 1)
        b.vx = -speed if b.wall == heading or no_floor else speed
        return []

    def render(self, x: int, y: int) -> None:
        step = (self.timer // 8) % 2
        pyxel.rect(x + 1 + step, y + 7, 4, 3, 4)
        pyxel.rect(x + 7 - step, y + 7, 4, 3, 4)
        pyxel.rect(x + 2, y + 4, 8, 4, 13)
        pyxel.circ(x + 6, y + 4, 4, 10)
        pyxel.rect(x, y + 5, 12, 2, 9)
        eye = x + 3 if self.body.vx < 0 else x + 8
        pyxel.rect(eye, y + 7, 1, 2, 0)


class Flyer(Enemy):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(Body(x, y, 12, 8), hp=2)
        self.home_y = y

    def act(self, player: Player, level: Level) -> list[Shot]:
        b = self.body
        dx = player.body.cx - b.cx
        if abs(dx) < 96:
            b.x += math.copysign(0.7, dx)
            target = player.body.cy - b.h / 2
            b.y += max(-0.6, min(0.6, target - b.y))
        else:
            b.y = self.home_y + math.sin(self.timer / 12) * 6
        return []

    def render(self, x: int, y: int) -> None:
        flap = 3 if (self.timer // 5) % 2 else -2
        pyxel.tri(x + 4, y + 3, x - 2, y + 3 + flap, x + 3, y + 6, 2)
        pyxel.tri(x + 8, y + 3, x + 14, y + 3 + flap, x + 9, y + 6, 2)
        pyxel.circ(x + 6, y + 4, 3, 14)
        pyxel.pset(x + 5, y + 3, 8)
        pyxel.pset(x + 7, y + 3, 8)


class Turret(Enemy):
    contact_damage = 3

    def __init__(self, x: float, y: float) -> None:
        super().__init__(Body(x, y, 12, 12), hp=4)
        self.facing = -1

    def act(self, player: Player, level: Level) -> list[Shot]:
        b = self.body
        self.facing = 1 if player.body.cx > b.cx else -1
        if self.timer % 100 != 0 or abs(player.body.cx - b.cx) > 160:
            return []
        muzzle = b.x + b.w + 2 if self.facing > 0 else b.x - 2
        return [enemy_shot(muzzle, b.y + 4, self.facing * 2.0)]

    def render(self, x: int, y: int) -> None:
        pyxel.rect(x, y + 4, 12, 8, 13)
        pyxel.rect(x + 1, y + 5, 10, 2, 5)
        pyxel.circ(x + 6, y + 4, 4, 5)
        barrel = x + 8 if self.facing > 0 else x - 2
        pyxel.rect(barrel, y + 3, 6, 3, 1)
        ready = self.timer % 100 > 70
        pyxel.pset(x + 6, y + 3, 8 if ready else 2)


def ground_y(row: int, height: int) -> float:
    return (row + 1) * TILE - height
