from collections.abc import Callable

import pyxel

from game.audio import Sfx
from game.config import (
    DASH_FRAMES,
    DASH_SPEED,
    FULL_CHARGE,
    HALF_CHARGE,
    HEIGHT,
    HURT_FRAMES,
    INVULN_FRAMES,
    JUMP_CUT,
    JUMP_SPEED,
    KICK_FRAMES,
    KICK_SPEED,
    PLAYER_MAX_HP,
    RUN_SPEED,
    WALL_JUMP_SPEED,
    WALL_SLIDE_SPEED,
)
from game.controls import Controls
from game.level import Level
from game.physics import Body, apply_gravity, move
from game.shot import Shot, buster_shot

type Part = Callable[[int, int, int, int, int], None]


class Player:
    def __init__(self, x: float, y: float) -> None:
        self.body = Body(x, y, 10, 16)
        self.facing = 1
        self.hp = PLAYER_MAX_HP
        self.charge = 0
        self.dash_timer = 0
        self.dash_jump = False
        self.kick_timer = 0
        self.hurt_timer = 0
        self.invuln = 0
        self.shoot_timer = 0
        self.sliding = False
        self.sfx: list[Sfx] = []

    @property
    def alive(self) -> bool:
        return self.hp > 0

    @property
    def charge_level(self) -> int:
        if self.charge >= FULL_CHARGE:
            return 3
        if self.charge >= HALF_CHARGE:
            return 2
        return 1

    def update(self, c: Controls, level: Level) -> list[Shot]:
        b = self.body
        self.invuln = max(0, self.invuln - 1)
        self.shoot_timer = max(0, self.shoot_timer - 1)
        if self.hurt_timer > 0:
            self.hurt_timer -= 1
        elif self.kick_timer > 0:
            self.kick_timer -= 1
        else:
            self._run(c)
            self._jump(c)
        apply_gravity(b)
        self.sliding = not b.on_ground and b.wall != 0 and b.wall == c.direction and b.vy > 0
        if self.sliding:
            b.vy = min(b.vy, WALL_SLIDE_SPEED)
            self.dash_jump = False
        move(b, level)
        if b.on_ground:
            self.dash_jump = False
        if level.hits(b.x + 1, b.y + 1, b.w - 2, b.h - 1, "^") or b.y > HEIGHT + 16:
            self.hp = 0
        return self._shoot(c) if self.hurt_timer == 0 else []

    def hurt(self, damage: int, from_x: float) -> None:
        if self.invuln > 0 or not self.alive:
            return
        self.hp = max(0, self.hp - damage)
        self.invuln = INVULN_FRAMES
        self.hurt_timer = HURT_FRAMES
        self.dash_timer = 0
        self.kick_timer = 0
        self.facing = 1 if from_x > self.body.cx else -1
        self.body.vx = -self.facing * 1.0
        self.body.vy = -1.5
        self.sfx.append(Sfx.HURT)

    def _run(self, c: Controls) -> None:
        b = self.body
        direction = c.direction
        if direction and direction != self.facing:
            self.dash_timer = 0
        if direction:
            self.facing = direction
        if c.dash and b.on_ground and self.dash_timer == 0:
            self.dash_timer = DASH_FRAMES
            self.sfx.append(Sfx.DASH)
        if self.dash_timer > 0 and b.on_ground and c.dash_held:
            self.dash_timer -= 1
            b.vx = self.facing * DASH_SPEED
            return
        self.dash_timer = 0
        b.vx = direction * (DASH_SPEED if self.dash_jump else RUN_SPEED)

    def _jump(self, c: Controls) -> None:
        b = self.body
        if c.jump and b.on_ground:
            b.vy = JUMP_SPEED
            self.dash_jump = self.dash_timer > 0
            self.dash_timer = 0
            self.sfx.append(Sfx.JUMP)
        elif c.jump and b.wall != 0:
            b.vy = WALL_JUMP_SPEED
            b.vx = -b.wall * KICK_SPEED
            self.facing = -b.wall
            self.kick_timer = KICK_FRAMES
            self.dash_jump = c.dash_held
            self.sfx.append(Sfx.JUMP)
        elif not c.jump_held and b.vy < JUMP_CUT:
            b.vy = JUMP_CUT

    def _shoot(self, c: Controls) -> list[Shot]:
        shots = []
        if c.shoot:
            shots.append(self._fire(1))
        if c.shoot_held:
            self.charge += 1
        else:
            if self.charge_level > 1:
                shots.append(self._fire(self.charge_level))
            self.charge = 0
        return shots

    def _fire(self, level: int) -> Shot:
        b = self.body
        self.shoot_timer = 16
        self.sfx.append(Sfx.SHOT if level == 1 else Sfx.CHARGED)
        muzzle = b.x + b.w + 2 if self.facing > 0 else b.x - 2
        return buster_shot(muzzle, b.y + 8, self.facing, level)

    def draw(self) -> None:
        if not self.alive or (self.invuln > 0 and self.invuln % 4 < 2):
            return
        if self.charge >= HALF_CHARGE and self.charge % 4 < 2:
            pyxel.pal(6, 11 if self.charge_level == 3 else 10)
        b = self.body
        x, y = round(b.x), round(b.y)
        part = self._part(x, y)
        running = b.on_ground and b.vx != 0 and self.dash_timer == 0
        step = (pyxel.frame_count // 6) % 2 if running else 0
        if self.dash_timer > 0:
            part(0, 13, 6, 3, 5)
            part(5, 13, 6, 3, 6)
            y += 2
        elif not b.on_ground:
            part(1, 11, 3, 3, 5)
            part(5, 10, 4, 4, 5)
            part(0, 13, 4, 2, 6)
            part(5, 13, 4, 2, 6)
        else:
            part(1 + step, 11, 3, 5, 5)
            part(6 - step, 11, 3, 5, 5)
            part(0 + step, 14, 4, 2, 6)
            part(6 - step, 14, 4, 2, 6)
        self._draw_upper(self._part(x, y))
        pyxel.pal()

    def _draw_upper(self, part: Part) -> None:
        part(1, 0, 8, 6, 6)
        part(3, 0, 4, 1, 7)
        part(1, 2, 2, 2, 8)
        part(4, 2, 5, 4, 15)
        part(7, 3, 1, 2, 1)
        part(1, 6, 8, 5, 5)
        part(2, 6, 5, 3, 6)
        arm = 5 if self.shoot_timer > 0 or self.charge >= HALF_CHARGE else 3
        part(7, 7, arm, 3, 6)
        part(6 + arm, 7, 2, 3, 5)
        if self.sliding:
            part(9, 2, 1, 4, 7)

    def _part(self, x: int, y: int) -> Part:
        w = self.body.w

        def draw(px: int, py: int, pw: int, ph: int, col: int) -> None:
            left = x + px if self.facing > 0 else x + w - px - pw
            pyxel.rect(left, y + py, pw, ph, col)

        return draw

