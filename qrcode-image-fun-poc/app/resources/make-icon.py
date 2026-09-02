import subprocess
from pathlib import Path

import cv2
import numpy as np

SIZE = 1024
CORNER = 232
GRID = 9
UNIT = 80
MARGIN = (SIZE - GRID * UNIT) // 2
INK = (28, 27, 25)
PAPER = (250, 249, 247)
BUILD = Path(__file__).resolve().parent
ICONSET = BUILD / "icon.iconset"


def rounded_alpha() -> np.ndarray:
    alpha = np.zeros((SIZE, SIZE), np.uint8)
    cv2.rectangle(alpha, (CORNER, 0), (SIZE - CORNER, SIZE), 255, -1)
    cv2.rectangle(alpha, (0, CORNER), (SIZE, SIZE - CORNER), 255, -1)
    for cx in (CORNER, SIZE - CORNER):
        for cy in (CORNER, SIZE - CORNER):
            cv2.circle(alpha, (cx, cy), CORNER, 255, -1)
    return alpha


def gradient() -> np.ndarray:
    top = np.array([47, 85, 192], np.float32)
    bottom = np.array([90, 60, 170], np.float32)
    ramp = np.linspace(0, 1, SIZE, dtype=np.float32)[:, None, None]
    return np.repeat(top * (1 - ramp) + bottom * ramp, SIZE, axis=1).astype(np.uint8)


def cell(col: int, row: int) -> tuple[int, int]:
    return MARGIN + col * UNIT, MARGIN + row * UNIT


def finder(canvas: np.ndarray, col: int, row: int) -> None:
    x, y = cell(col, row)
    side = UNIT * 3
    cv2.rectangle(canvas, (x, y), (x + side, y + side), PAPER, -1)
    inset = UNIT // 2
    cv2.rectangle(
        canvas,
        (x + inset, y + inset),
        (x + side - inset, y + side - inset),
        INK,
        -1,
    )
    cv2.rectangle(
        canvas,
        (x + UNIT, y + UNIT),
        (x + side - UNIT, y + side - UNIT),
        PAPER,
        -1,
    )


def occupied(col: int, row: int) -> bool:
    corners = [(0, 0), (GRID - 3, 0), (0, GRID - 3)]
    return any(c <= col < c + 3 and r <= row < r + 3 for c, r in corners)


def draw() -> np.ndarray:
    canvas = gradient()
    for col, row in [(0, 0), (GRID - 3, 0), (0, GRID - 3)]:
        finder(canvas, col, row)

    rng = np.random.default_rng(11)
    for row in range(GRID):
        for col in range(GRID):
            if occupied(col, row) or rng.random() < 0.48:
                continue
            x, y = cell(col, row)
            cv2.circle(
                canvas,
                (x + UNIT // 2, y + UNIT // 2),
                int(UNIT * 0.3),
                PAPER,
                -1,
                cv2.LINE_AA,
            )
    return canvas


def main() -> None:
    rgba = np.dstack([draw(), rounded_alpha()])
    ICONSET.mkdir(exist_ok=True)
    cv2.imwrite(str(BUILD / "icon.png"), rgba)
    for size in (16, 32, 128, 256, 512):
        cv2.imwrite(
            str(ICONSET / f"icon_{size}x{size}.png"),
            cv2.resize(rgba, (size, size), interpolation=cv2.INTER_AREA),
        )
        cv2.imwrite(
            str(ICONSET / f"icon_{size}x{size}@2x.png"),
            cv2.resize(rgba, (size * 2, size * 2), interpolation=cv2.INTER_AREA),
        )
    subprocess.run(
        ["iconutil", "-c", "icns", str(ICONSET), "-o", str(BUILD / "icon.icns")],
        check=True,
    )


if __name__ == "__main__":
    main()
