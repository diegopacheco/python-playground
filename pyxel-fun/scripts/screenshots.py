from pathlib import Path

import pyxel

from game.app import App, State
from game.config import FPS, HEIGHT, TITLE, WIDTH
from game.controls import Controls

OUT = Path(__file__).resolve().parent.parent / "printscreens"


def save(app: App, name: str) -> None:
    app.draw()
    pyxel.screen.save(str(OUT / name), 3)


def play(app: App, frames: int, controls: Controls) -> None:
    for _ in range(frames):
        app.step(controls)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    pyxel.init(WIDTH, HEIGHT, title=TITLE, fps=FPS, headless=True)
    app = App()
    save(app, "title.png")

    app.new_game()
    play(app, 40, Controls())
    for i in range(130):
        app.step(Controls(right=i > 60, shoot=i % 8 == 0))
    play(app, 14, Controls(right=True, jump=True, jump_held=True, shoot=True))
    save(app, "action.png")

    play(app, 85, Controls(shoot_held=True))
    save(app, "charge.png")

    app.world.checkpoint = 2
    app.respawn()
    play(app, 90, Controls(right=True))
    for i in range(30):
        app.step(Controls(shoot=i % 6 == 0))
    save(app, "boss.png")

    app.state = State.OVER
    save(app, "game-over.png")


if __name__ == "__main__":
    main()
