from enum import Enum, auto

import pyxel

from game import audio
from game.config import FPS, HEIGHT, RESPAWN_FRAMES, START_LIVES, TITLE, WIDTH, WIN_FRAMES
from game.controls import Controls, read_controls, start_pressed
from game.hud import draw_hud
from game.layout import build_rows
from game.level import Level
from game.world import World


class State(Enum):
    TITLE = auto()
    PLAY = auto()
    WIN = auto()
    OVER = auto()


class App:
    def __init__(self) -> None:
        audio.setup()
        self.state = State.TITLE
        self.lives = START_LIVES
        self.world = World(Level(build_rows()))
        self.timer = 0

    def run(self) -> None:
        pyxel.run(self.update, self.draw)

    def new_game(self) -> None:
        self.lives = START_LIVES
        self.world = World(Level(build_rows()))
        self.state = State.PLAY
        self.timer = 0
        audio.start_music()

    def respawn(self) -> None:
        self.world = World(Level(build_rows()), self.world.checkpoint)
        self.timer = 0

    def update(self) -> None:
        match self.state:
            case State.TITLE | State.OVER:
                if start_pressed():
                    self.new_game()
            case State.PLAY:
                self.step(read_controls())
            case State.WIN:
                self.world.update(Controls())
                if start_pressed():
                    self.state = State.TITLE

    def step(self, controls: Controls) -> None:
        world = self.world
        world.update(controls)
        for sfx in world.sfx:
            audio.play(sfx)
        world.sfx.clear()
        if not world.player.alive or world.won:
            self.timer += 1
        if world.won and self.timer >= WIN_FRAMES:
            self.state = State.WIN
            audio.stop_music()
        elif not world.player.alive and self.timer >= RESPAWN_FRAMES:
            self.lives -= 1
            if self.lives > 0:
                self.respawn()
            else:
                self.state = State.OVER
                audio.stop_music()

    def draw(self) -> None:
        match self.state:
            case State.TITLE:
                self.draw_title()
            case State.PLAY:
                self.world.draw()
                draw_hud(self.world, self.lives)
            case State.WIN:
                self.world.draw()
                self.banner("MISSION COMPLETE", "PRESS ENTER", 11)
            case State.OVER:
                self.world.draw()
                self.banner("GAME OVER", "PRESS ENTER TO RETRY", 8)

    def draw_title(self) -> None:
        self.world.draw()
        pyxel.rect(0, 30, WIDTH, 64, 0)
        pyxel.line(0, 30, WIDTH, 30, 6)
        pyxel.line(0, 93, WIDTH, 93, 6)
        centered(40, TITLE.upper(), 12)
        centered(54, "A PYXEL PLATFORM ACTION GAME", 7)
        centered(68, "ARROWS MOVE  Z JUMP  X SHOOT  C DASH", 13)
        centered(78, "HOLD X TO CHARGE  JUMP ON WALLS TO CLIMB", 13)
        if pyxel.frame_count % 40 < 28:
            centered(HEIGHT - 40, "PRESS ENTER", 10)

    def banner(self, title: str, hint: str, col: int) -> None:
        pyxel.rect(0, 56, WIDTH, 40, 0)
        centered(64, title, col)
        centered(80, hint, 7)


def centered(y: int, text: str, col: int) -> None:
    pyxel.text((WIDTH - len(text) * 4) // 2, y, text, col)


def main() -> None:
    pyxel.init(WIDTH, HEIGHT, title=TITLE, fps=FPS)
    App().run()
