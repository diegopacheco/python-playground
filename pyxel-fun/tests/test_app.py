import unittest

import pyxel

from game.app import App, State
from game.config import FPS, HEIGHT, START_LIVES, TITLE, WIDTH
from game.controls import Controls
from tests.helpers import IDLE

pyxel.init(WIDTH, HEIGHT, title=TITLE, fps=FPS, headless=True)


class AppTest(unittest.TestCase):
    def test_every_state_draws_without_errors(self) -> None:
        app = App()
        app.draw()
        app.new_game()
        for i in range(120):
            app.step(Controls(right=True, shoot=i % 10 == 0, shoot_held=True))
            app.draw()
        for state in (State.WIN, State.OVER):
            app.state = state
            app.draw()

    def test_death_costs_a_life_and_respawns_full_health(self) -> None:
        app = App()
        app.new_game()
        app.world.player.hp = 0
        for _ in range(200):
            app.step(IDLE)
        self.assertEqual(app.lives, START_LIVES - 1)
        self.assertTrue(app.world.player.alive)

    def test_losing_the_last_life_ends_the_game(self) -> None:
        app = App()
        app.new_game()
        app.lives = 1
        app.world.player.hp = 0
        for _ in range(200):
            app.step(IDLE)
        self.assertIs(app.state, State.OVER)


if __name__ == "__main__":
    unittest.main()
