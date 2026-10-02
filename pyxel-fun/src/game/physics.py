import math
from dataclasses import dataclass

from game.config import GRAVITY, MAX_FALL, TILE
from game.level import Level


@dataclass(slots=True)
class Body:
    x: float
    y: float
    w: int
    h: int
    vx: float = 0.0
    vy: float = 0.0
    on_ground: bool = False
    wall: int = 0

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    def overlaps(self, other: Body) -> bool:
        return (
            self.x < other.x + other.w
            and other.x < self.x + self.w
            and self.y < other.y + other.h
            and other.y < self.y + self.h
        )


def apply_gravity(body: Body) -> None:
    body.vy = min(body.vy + GRAVITY, MAX_FALL)


def move(body: Body, level: Level) -> None:
    body.x += body.vx
    if level.hits(body.x, body.y, body.w, body.h):
        if body.vx > 0:
            body.x = math.floor((body.x + body.w) / TILE) * TILE - body.w
        elif body.vx < 0:
            body.x = (math.floor(body.x / TILE) + 1) * TILE
        body.vx = 0.0

    body.y += body.vy
    body.on_ground = False
    if level.hits(body.x, body.y, body.w, body.h):
        if body.vy > 0:
            body.y = math.floor((body.y + body.h) / TILE) * TILE - body.h
            body.on_ground = True
        elif body.vy < 0:
            body.y = (math.floor(body.y / TILE) + 1) * TILE
        body.vy = 0.0
    elif (body.y + body.h) % TILE == 0 and level.hits(body.x, body.y + body.h, body.w, 1):
        body.on_ground = body.vy >= 0

    if level.hits(body.x + 1, body.y, body.w, body.h - 2):
        body.wall = 1
    elif level.hits(body.x - 1, body.y, body.w, body.h - 2):
        body.wall = -1
    else:
        body.wall = 0
