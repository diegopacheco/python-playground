import math
import random
from dataclasses import dataclass

import pyxel


@dataclass(slots=True)
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: int
    col: int
    size: float = 1.0

    def update(self) -> None:
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    def draw(self) -> None:
        if self.size <= 1:
            pyxel.pset(self.x, self.y, self.col)
        else:
            pyxel.circ(self.x, self.y, self.size, self.col)


def burst(x: float, y: float, colors: tuple[int, ...], count: int = 12) -> list[Particle]:
    parts = []
    for _ in range(count):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(0.5, 2.5)
        parts.append(
            Particle(
                x,
                y,
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                random.randint(12, 28),
                random.choice(colors),
                random.choice((1.0, 1.0, 2.0)),
            )
        )
    return parts


def ring(x: float, y: float, colors: tuple[int, ...], count: int = 16) -> list[Particle]:
    return [
        Particle(
            x,
            y,
            math.cos(math.tau * i / count) * speed,
            math.sin(math.tau * i / count) * speed,
            80,
            colors[i % len(colors)],
            2.0,
        )
        for speed in (1.0, 2.0)
        for i in range(count)
    ]
