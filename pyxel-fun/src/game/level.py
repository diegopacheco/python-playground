import math
from typing import NamedTuple

import pyxel

from game.config import TILE, WIDTH

MARKER_KINDS = "PCAWFTB"
EPS = 0.001


class Spawn(NamedTuple):
    kind: str
    col: int
    row: int


class Level:
    def __init__(self, rows: list[str]) -> None:
        if len({len(r) for r in rows}) != 1:
            raise ValueError("level rows must have the same width")
        self.grid = [list(r) for r in rows]
        self.rows = len(rows)
        self.cols = len(rows[0])
        self.spawns: list[Spawn] = []
        for row, line in enumerate(self.grid):
            for col, ch in enumerate(line):
                if ch in MARKER_KINDS:
                    self.spawns.append(Spawn(ch, col, row))
                    line[col] = "."

    @property
    def width_px(self) -> int:
        return self.cols * TILE

    def find(self, kind: str) -> list[Spawn]:
        return [s for s in self.spawns if s.kind == kind]

    def tile(self, col: int, row: int) -> str:
        if col < 0 or col >= self.cols:
            return "#"
        if row < 0 or row >= self.rows:
            return "."
        return self.grid[row][col]

    def hits(self, x: float, y: float, w: float, h: float, kinds: str = "#") -> bool:
        c0, c1 = math.floor(x / TILE), math.floor((x + w - EPS) / TILE)
        r0, r1 = math.floor(y / TILE), math.floor((y + h - EPS) / TILE)
        return any(
            self.tile(c, r) in kinds
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
        )

    def fill(self, col: int, row: int, w: int, h: int, ch: str) -> None:
        for r in range(row, row + h):
            for c in range(col, col + w):
                self.grid[r][c] = ch

    def draw(self, cam_x: float) -> None:
        first = max(0, int(cam_x) // TILE)
        last = min(self.cols, first + WIDTH // TILE + 2)
        for row in range(self.rows):
            for col in range(first, last):
                match self.grid[row][col]:
                    case "#":
                        self._draw_solid(col, row)
                    case "^":
                        self._draw_spike(col, row)

    def _draw_solid(self, col: int, row: int) -> None:
        x, y = col * TILE, row * TILE
        pyxel.rect(x, y, TILE, TILE, 1)
        if self.tile(col, row - 1) != "#":
            pyxel.rect(x, y, TILE, 2, 6)
            pyxel.line(x, y + 2, x + TILE - 1, y + 2, 5)
        elif (col + row) % 2 == 0:
            pyxel.pset(x + 3, y + 4, 5)
        if self.tile(col - 1, row) != "#":
            pyxel.line(x, y, x, y + TILE - 1, 5)
        if self.tile(col + 1, row) != "#":
            pyxel.line(x + TILE - 1, y, x + TILE - 1, y + TILE - 1, 5)

    def _draw_spike(self, col: int, row: int) -> None:
        x, y = col * TILE, row * TILE
        pyxel.tri(x, y + 7, x + 1.5, y, x + 3, y + 7, 13)
        pyxel.tri(x + 4, y + 7, x + 5.5, y, x + 7, y + 7, 7)
