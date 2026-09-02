import numpy as np
import segno

VERSION = 5
ERROR = "h"
MODULES = 37
RENDER_PX = 24
RENDER_SIDE = MODULES * RENDER_PX

STYLES = [
    {"field": 0.00, "dot": 0.42},
    {"field": 0.15, "dot": 0.46},
    {"field": 0.35, "dot": 0.50},
    {"field": 1.00, "dot": 0.50},
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


def _upscale(cells: np.ndarray) -> np.ndarray:
    return np.kron(cells, np.ones((RENDER_PX, RENDER_PX), dtype=cells.dtype))


def _square(image: np.ndarray) -> np.ndarray:
    height, width = image.shape[:2]
    side = min(height, width)
    top = (height - side) // 2
    left = (width - side) // 2
    return image[top : top + side, left : left + side]


def _dot_alpha(radius_ratio: float) -> np.ndarray:
    axis = np.arange(RENDER_PX) + 0.5 - RENDER_PX / 2
    yy, xx = np.meshgrid(axis, axis, indexing="ij")
    distance = np.sqrt(xx**2 + yy**2) / RENDER_PX
    edge = np.clip((radius_ratio - distance) * RENDER_PX + 0.5, 0.0, 1.0)
    return np.tile(edge, (MODULES, MODULES))


def render(payload: str, image: np.ndarray, field: float, dot: float) -> np.ndarray:
    import cv2

    dark = matrix(payload)
    target = _upscale(np.where(dark, 0.0, 255.0)).astype(np.float32)[:, :, None]

    canvas = cv2.resize(
        _square(image), (RENDER_SIDE, RENDER_SIDE), interpolation=cv2.INTER_AREA
    ).astype(np.float32)

    alpha = _dot_alpha(dot)[:, :, None]
    painted = canvas * (1.0 - field) + target * field
    out = painted * (1.0 - alpha) + target * alpha

    out = np.where(_upscale(function_mask())[:, :, None], target, out)
    return np.clip(out, 0, 255).astype(np.uint8)
