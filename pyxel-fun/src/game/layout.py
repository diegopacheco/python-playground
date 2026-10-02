from typing import Final

COLS: Final = 224
ROWS: Final = 20

type Block = tuple[str, int, int, int, int]
type Marker = tuple[str, int, int]

BLOCKS: Final[list[Block]] = [
    ("#", 0, 17, 42, 3),
    ("#", 14, 13, 5, 1),
    ("#", 26, 11, 6, 1),
    ("^", 42, 19, 5, 1),
    ("#", 47, 17, 41, 3),
    ("#", 52, 15, 4, 2),
    ("#", 58, 13, 4, 4),
    ("#", 64, 15, 4, 2),
    ("#", 72, 12, 6, 1),
    ("#", 88, 7, 16, 13),
    ("#", 104, 17, 12, 3),
    ("#", 116, 18, 22, 2),
    ("^", 116, 17, 22, 1),
    ("#", 118, 13, 4, 1),
    ("#", 125, 11, 4, 1),
    ("#", 132, 13, 4, 1),
    ("#", 138, 17, 54, 3),
    ("#", 150, 14, 8, 3),
    ("#", 166, 12, 3, 5),
    ("#", 176, 15, 6, 2),
    ("#", 192, 17, 32, 3),
]

MARKERS: Final[list[Marker]] = [
    ("P", 3, 16),
    ("W", 20, 16),
    ("F", 30, 8),
    ("W", 36, 16),
    ("T", 59, 12),
    ("W", 70, 16),
    ("F", 76, 8),
    ("W", 80, 16),
    ("W", 96, 6),
    ("C", 106, 16),
    ("F", 126, 7),
    ("F", 133, 8),
    ("T", 140, 16),
    ("W", 154, 13),
    ("F", 162, 8),
    ("W", 172, 16),
    ("T", 184, 16),
    ("C", 188, 16),
    ("A", 192, 0),
    ("B", 214, 16),
]


def build_rows() -> list[str]:
    grid = [["."] * COLS for _ in range(ROWS)]
    for ch, col, row, w, h in BLOCKS:
        for r in range(row, row + h):
            for c in range(col, col + w):
                grid[r][c] = ch
    for ch, col, row in MARKERS:
        grid[row][col] = ch
    return ["".join(r) for r in grid]
