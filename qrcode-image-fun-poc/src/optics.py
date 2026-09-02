import cv2
import numpy as np

import page

CAMERA_PAGE_WIDTH = 1920
RECTIFIED_SCALE = 0.5
GATE_TILTS = (
    ((0.03, 0.01), (-0.01, 0.03), (-0.03, -0.01), (0.01, -0.03)),
    ((0.05, 0.02), (-0.02, 0.05), (-0.05, -0.02), (0.02, -0.05)),
    ((0.02, 0.05), (-0.05, 0.02), (-0.02, -0.05), (0.05, -0.02)),
)
_detector = cv2.QRCodeDetector()


def decode(image: np.ndarray) -> tuple[str, np.ndarray] | None:
    payload, points, _ = _detector.detectAndDecode(image)
    if not payload or points is None:
        return None
    return payload, points.reshape(4, 2).astype(np.float32)


def simulate_camera(rendered: np.ndarray) -> np.ndarray:
    height = int(rendered.shape[0] * CAMERA_PAGE_WIDTH / rendered.shape[1])
    shrunk = cv2.resize(rendered, (CAMERA_PAGE_WIDTH, height), interpolation=cv2.INTER_AREA)
    return cv2.GaussianBlur(shrunk, (3, 3), 0)


def tilt(frame: np.ndarray, offsets: tuple) -> np.ndarray:
    height, width = frame.shape[:2]
    flat = np.float32([[0, 0], [width, 0], [width, height], [0, height]])
    leaning = np.float32(
        [
            [corner[0] + dx * width, corner[1] + dy * height]
            for corner, (dx, dy) in zip(flat, offsets)
        ]
    )
    return cv2.warpPerspective(
        frame,
        cv2.getPerspectiveTransform(flat, leaning),
        (width, height),
        borderValue=(235, 235, 235),
    )


def passes_gate(rendered: np.ndarray, expected: str) -> bool:
    straight = simulate_camera(rendered)
    leaning = [
        cv2.GaussianBlur(tilt(straight, offsets), (3, 3), 0) for offsets in GATE_TILTS
    ]
    for frame in [straight, *leaning]:
        found = decode(frame)
        if found is None or found[0] != expected:
            return False
    return True


def rectify(capture: np.ndarray, corners: np.ndarray) -> np.ndarray:
    target = page.CODE_CORNERS * RECTIFIED_SCALE
    homography = cv2.getPerspectiveTransform(corners, target)
    size = (int(page.PAGE_W * RECTIFIED_SCALE), int(page.PAGE_H * RECTIFIED_SCALE))
    return cv2.warpPerspective(capture, homography, size, borderValue=(255, 255, 255))
