from enum import IntEnum

import pyxel


class Sfx(IntEnum):
    SHOT = 0
    CHARGED = 1
    JUMP = 2
    DASH = 3
    HURT = 4
    EXPLODE = 5
    ENEMY_SHOT = 6
    HIT = 7


SFX_DATA: dict[Sfx, tuple[str, str, str, str, int]] = {
    Sfx.SHOT: ("a3e3", "p", "4", "f", 3),
    Sfx.CHARGED: ("c2g2c3g3", "s", "6", "f", 4),
    Sfx.JUMP: ("c2e2g2", "p", "3", "s", 3),
    Sfx.DASH: ("a1a1a1", "n", "4", "f", 4),
    Sfx.HURT: ("c3g2c2", "s", "6", "f", 5),
    Sfx.EXPLODE: ("c2a1f1c1", "n", "7", "f", 8),
    Sfx.ENEMY_SHOT: ("e2c2", "p", "3", "f", 4),
    Sfx.HIT: ("g3", "n", "4", "f", 3),
}

MELODY = "g3g3a#3c4rc4a#3g3f3f3g3a#3ra#3g3f3d#3d#3f3g3rg3a#3c4d4c4b3g3b3c4d4r"
BASS = "c2c2c3c2c2c2c3c2a#1a#1a#2a#1a#1a#1a#2a#1g#1g#1g#2g#1g#1g#1g#2g#1g1g1g2g1g1g1g2g1"
DRUMS = "a1ra4ra1a1a4r" * 4

MUSIC_SOUNDS = (10, 11, 12)
SFX_CHANNELS = (3, 2)


def setup() -> None:
    for sfx, (notes, tones, volumes, effects, speed) in SFX_DATA.items():
        pyxel.sounds[sfx].set(notes, tones, volumes, effects, speed)
    pyxel.sounds[10].set(MELODY, "s", "3", "n", 14)
    pyxel.sounds[11].set(BASS, "t", "5", "n", 14)
    pyxel.sounds[12].set(DRUMS, "n", "3", "f", 14)
    pyxel.musics[0].set(*[[s] for s in MUSIC_SOUNDS])


def play(sfx: Sfx) -> None:
    channel = SFX_CHANNELS[0] if sfx in (Sfx.SHOT, Sfx.CHARGED) else SFX_CHANNELS[1]
    pyxel.play(channel, sfx, resume=True)


def start_music() -> None:
    pyxel.playm(0, loop=True)


def stop_music() -> None:
    pyxel.stop()
