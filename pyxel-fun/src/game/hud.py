import pyxel

from game.config import BOSS_MAX_HP, PLAYER_MAX_HP, WIDTH
from game.world import World


def draw_bar(x: int, y: int, value: int, maximum: int, col: int, label: str) -> None:
    height = maximum * 2 + 3
    pyxel.rect(x, y, 7, height, 0)
    pyxel.rectb(x, y, 7, height, 7)
    for i in range(maximum):
        seg_y = y + height - 3 - i * 2
        pyxel.line(x + 2, seg_y, x + 4, seg_y, col if i < value else 1)
    pyxel.rect(x - 1, y + height, 9, 7, 5)
    pyxel.text(x + 2, y + height + 1, label, 7)


def draw_hud(world: World, lives: int) -> None:
    draw_bar(8, 16, world.player.hp, PLAYER_MAX_HP, 10, "X")
    pyxel.text(6, 4, f"x{lives}", 7)
    if world.boss_fight and world.boss is not None:
        draw_bar(WIDTH - 16, 16, world.boss.hp, BOSS_MAX_HP, 8, "B")
    if world.player.charge_level > 1:
        col = 11 if world.player.charge_level == 3 else 10
        pyxel.text(22, 4, "CHARGE" + "!" * (world.player.charge_level - 1), col)
