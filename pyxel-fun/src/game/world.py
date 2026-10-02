from collections.abc import Callable

import pyxel

from game.audio import Sfx
from game.boss import Boss
from game.config import HEIGHT, TILE, WIDTH
from game.controls import Controls
from game.enemies import Enemy, Flyer, Turret, Walker, ground_y
from game.level import Level, Spawn
from game.particles import Particle, burst, ring
from game.player import Player
from game.shot import Shot

ENEMY_TYPES: dict[str, Callable[[float, float], Enemy]] = {"W": Walker, "F": Flyer, "T": Turret, "B": Boss}
ENEMY_SIZES: dict[str, int] = {"W": 10, "T": 12, "B": 24}
ACTIVE_MARGIN = 48


class World:
    def __init__(self, level: Level, checkpoint: int = 0) -> None:
        self.level = level
        self.checkpoints = [level.find("P")[0], *level.find("C")]
        self.checkpoint = min(checkpoint, len(self.checkpoints) - 1)
        start = self.checkpoints[self.checkpoint]
        self.player = Player(start.col * TILE, ground_y(start.row, 16))
        self.enemies = [self._spawn(s) for s in level.spawns if s.kind in ENEMY_TYPES]
        self.boss = next((e for e in self.enemies if isinstance(e, Boss)), None)
        self.arena_col = level.find("A")[0].col
        self.shots: list[Shot] = []
        self.particles: list[Particle] = []
        self.sfx: list[Sfx] = []
        self.cam_x = 0.0
        self.frame = 0
        self._update_camera()

    @property
    def boss_fight(self) -> bool:
        return self.boss is not None and self.boss.active

    @property
    def won(self) -> bool:
        return self.boss is not None and not self.boss.alive

    def update(self, c: Controls) -> None:
        self.frame += 1
        if self.player.alive:
            self.shots.extend(self.player.update(c, self.level))
            if not self.player.alive:
                self.particles.extend(ring(self.player.body.cx, self.player.body.cy, (6, 12, 7)))
                self.sfx.append(Sfx.EXPLODE)
        for enemy in self.enemies:
            if self._near_camera(enemy):
                fired = enemy.update(self.player, self.level)
                if fired:
                    self.sfx.append(Sfx.ENEMY_SHOT)
                self.shots.extend(fired)
        for shot in self.shots:
            shot.update(self.level)
        self._collide()
        self._cleanup()
        self._update_checkpoint()
        self._update_arena()
        self._update_camera()
        self.sfx.extend(self.player.sfx)
        self.player.sfx.clear()

    def _spawn(self, s: Spawn) -> Enemy:
        kind = ENEMY_TYPES[s.kind]
        x = s.col * TILE
        y = ground_y(s.row, ENEMY_SIZES[s.kind]) if s.kind in ENEMY_SIZES else s.row * TILE
        return kind(x, y)

    def _near_camera(self, enemy: Enemy) -> bool:
        x = enemy.body.x
        return self.cam_x - ACTIVE_MARGIN < x < self.cam_x + WIDTH + ACTIVE_MARGIN

    def _collide(self) -> None:
        player = self.player
        for shot in self.shots:
            if not shot.alive:
                continue
            if shot.friendly:
                for enemy in self.enemies:
                    if enemy.alive and self._near_camera(enemy) and shot.body.overlaps(enemy.body):
                        enemy.hit(shot.damage)
                        self.sfx.append(Sfx.HIT)
                        shot.alive = not enemy.alive and shot.damage >= 4
                        break
            elif player.alive and shot.body.overlaps(player.body):
                player.hurt(shot.damage, shot.body.cx)
                shot.alive = False
        for enemy in self.enemies:
            if enemy.alive and player.alive and enemy.body.overlaps(player.body):
                player.hurt(enemy.contact_damage, enemy.body.cx)

    def _cleanup(self) -> None:
        for enemy in self.enemies:
            if not enemy.alive:
                b = enemy.body
                if enemy.is_boss:
                    self.particles.extend(ring(b.cx, b.cy, (8, 9, 10, 7), 24))
                self.particles.extend(burst(b.cx, b.cy, (8, 9, 10, 7)))
                self.sfx.append(Sfx.EXPLODE)
        self.enemies = [e for e in self.enemies if e.alive]
        left, right = self.cam_x - 32, self.cam_x + WIDTH + 32
        self.shots = [
            s for s in self.shots if s.alive and left < s.body.x < right and -32 < s.body.y < HEIGHT + 32
        ]
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.life > 0]

    def _update_checkpoint(self) -> None:
        for i, cp in enumerate(self.checkpoints):
            if i > self.checkpoint and self.player.body.x >= cp.col * TILE:
                self.checkpoint = i

    def _update_arena(self) -> None:
        if self.boss is None or self.boss.active:
            return
        if self.player.body.x > (self.arena_col + 2) * TILE:
            self.boss.active = True
            self.level.fill(self.arena_col, 0, 1, 17, "#")

    def _update_camera(self) -> None:
        low = self.arena_col * TILE if self.boss_fight else 0.0
        high = self.level.width_px - WIDTH
        target = self.player.body.cx - WIDTH / 2
        self.cam_x = max(low, min(high, target))

    def draw(self) -> None:
        self._draw_background()
        pyxel.camera(self.cam_x, 0)
        self.level.draw(self.cam_x)
        for enemy in self.enemies:
            enemy.draw()
        self.player.draw()
        for shot in self.shots:
            shot.draw()
        for p in self.particles:
            p.draw()
        pyxel.camera()

    def _draw_background(self) -> None:
        pyxel.cls(0)
        pyxel.circ(200, 28, 10, 7)
        pyxel.circ(204, 25, 9, 0)
        for y in range(64, HEIGHT, 6):
            pyxel.line(0, y, WIDTH, y, 1)
        far = self.cam_x * 0.25
        for i in range(WIDTH // 40 + 2):
            x = i * 40 - far % 40
            building = i + int(far // 40)
            h = 30 + (building * 37) % 50
            pyxel.rect(x, HEIGHT - 24 - h, 28, h, 5)
            for wy in range(HEIGHT - 20 - h, HEIGHT - 28, 8):
                pyxel.pset(x + 6, wy, 10 if (wy + building) % 3 else 1)
                pyxel.pset(x + 18, wy, 1)
