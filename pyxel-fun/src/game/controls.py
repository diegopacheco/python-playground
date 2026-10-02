from dataclasses import dataclass

import pyxel


@dataclass(frozen=True, slots=True)
class Controls:
    left: bool = False
    right: bool = False
    jump: bool = False
    jump_held: bool = False
    shoot: bool = False
    shoot_held: bool = False
    dash: bool = False
    dash_held: bool = False

    @property
    def direction(self) -> int:
        return int(self.right) - int(self.left)


def _held(*keys: int) -> bool:
    return any(pyxel.btn(k) for k in keys)


def _pressed(*keys: int) -> bool:
    return any(pyxel.btnp(k) for k in keys)


JUMP_KEYS = (pyxel.KEY_Z, pyxel.KEY_SPACE, pyxel.GAMEPAD1_BUTTON_A)
SHOOT_KEYS = (pyxel.KEY_X, pyxel.GAMEPAD1_BUTTON_B)
DASH_KEYS = (pyxel.KEY_C, pyxel.GAMEPAD1_BUTTON_X)


def read_controls() -> Controls:
    return Controls(
        left=_held(pyxel.KEY_LEFT, pyxel.GAMEPAD1_BUTTON_DPAD_LEFT),
        right=_held(pyxel.KEY_RIGHT, pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT),
        jump=_pressed(*JUMP_KEYS),
        jump_held=_held(*JUMP_KEYS),
        shoot=_pressed(*SHOOT_KEYS),
        shoot_held=_held(*SHOOT_KEYS),
        dash=_pressed(*DASH_KEYS),
        dash_held=_held(*DASH_KEYS),
    )


def start_pressed() -> bool:
    return _pressed(pyxel.KEY_RETURN, pyxel.GAMEPAD1_BUTTON_START)
