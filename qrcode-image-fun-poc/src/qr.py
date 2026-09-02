import numpy as np
import segno

VERSION = 5
ERROR = "h"
MODULES = 37
MODULE_PX = 8
CODE_PX = MODULES * MODULE_PX

STYLES = [
    {"bias": 0.45, "dot": 0.32},
    {"bias": 0.60, "dot": 0.38},
    {"bias": 0.75, "dot": 0.44},
    {"bias": 1.00, "dot": 0.50},
]


def matrix(payload: str) -> np.ndarray:
    code = segno.make(payload, version=VERSION, error=ERROR, boost_error=False)
    rows = [list(row) for row in code.matrix]
    return np.array(rows, dtype=bool)


def function_mask() -> np.ndarray:
    n = MODULES
    mask = np.zeros((n, n), dtype=bool)
    mask[0:9, 0:9] = True
    mask[0:9, n - 8 : n] = True
    mask[n - 8 : n, 0:9] = True
    mask[6, :] = True
    mask[:, 6] = True
    mask[n - 9 : n - 4, n - 9 : n - 4] = True
    return mask


def _upscale(mask: np.ndarray) -> np.ndarray:
    return np.kron(mask, np.ones((MODULE_PX, MODULE_PX), dtype=mask.dtype))


def _dot_mask(radius_ratio: float) -> np.ndarray:
    axis = np.arange(MODULE_PX) + 0.5 - MODULE_PX / 2
    yy, xx = np.meshgrid(axis, axis, indexing="ij")
    disk = (xx**2 + yy**2) <= (radius_ratio * MODULE_PX) ** 2
    return np.tile(disk, (MODULES, MODULES))


def render(payload: str, image: np.ndarray, bias: float, dot: float) -> np.ndarray:
    import cv2

    dark = matrix(payload)
    target = np.where(dark, 0.0, 255.0)
    target_px = _upscale(target).astype(np.float32)[:, :, None]

    canvas = cv2.resize(image, (CODE_PX, CODE_PX), interpolation=cv2.INTER_AREA)
    canvas = canvas.astype(np.float32)

    blended = canvas * (1.0 - bias) + target_px * bias

    solid = _upscale(function_mask()) | _dot_mask(dot)
    out = np.where(solid[:, :, None], target_px, blended)
    return np.clip(out, 0, 255).astype(np.uint8)
