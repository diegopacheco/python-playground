from game.controls import Controls
from game.level import Level

RIGHT = Controls(right=True)
LEFT = Controls(left=True)
IDLE = Controls()


def flat_level(width: int = 40, height: int = 20, ground: int = 17) -> Level:
    rows = ["." * width for _ in range(ground)] + ["#" * width for _ in range(height - ground)]
    rows[0] = "P" + rows[0][1:]
    return Level(rows)
