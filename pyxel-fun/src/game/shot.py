from dataclasses import dataclass

import pyxel

from game.level import Level
from game.physics import Body

SHOT_SIZES: dict[int, tuple[int, int]] = {1: (5, 4), 2: (9, 7), 3: (16, 12)}


@dataclass(slots=True)
class Shot:
    body: Body
    damage: int
    friendly: bool
    alive: bool = True

    def update(self, level: Level) -> None:
        b = self.body
        b.x += b.vx
        b.y += b.vy
        if level.hits(b.x, b.y, b.w, b.h):
            self.alive = False

    def draw(self) -> None:
        b = self.body
        if not self.friendly:
            pyxel.circ(b.cx, b.cy, b.w / 2, 9)
            pyxel.circ(b.cx, b.cy, b.w / 4, 10)
            return
        match self.damage:
            case 1:
                pyxel.elli(b.x, b.y, b.w, b.h, 10)
                pyxel.pset(b.cx, b.cy - 1, 7)
            case 2:
                pyxel.elli(b.x, b.y, b.w, b.h, 11)
                pyxel.elli(b.x + 2, b.y + 2, b.w - 4, b.h - 4, 7)
            case _:
                tail = -6 if b.vx > 0 else b.w
                pyxel.elli(b.x + tail, b.y + 3, 6, b.h - 6, 3)
                pyxel.elli(b.x, b.y, b.w, b.h, 11)
                pyxel.elli(b.x + 3, b.y + 3, b.w - 6, b.h - 6, 7)


def buster_shot(x: float, y: float, facing: int, level: int) -> Shot:
    w, h = SHOT_SIZES[level]
    left = x if facing > 0 else x - w
    body = Body(left, y - h / 2, w, h, vx=facing * (5.0 + level))
    return Shot(body, damage={1: 1, 2: 2, 3: 4}[level], friendly=True)


def enemy_shot(x: float, y: float, vx: float, vy: float = 0.0) -> Shot:
    return Shot(Body(x - 3, y - 3, 6, 6, vx=vx, vy=vy), damage=2, friendly=False)
