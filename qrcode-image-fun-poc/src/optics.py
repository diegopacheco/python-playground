import cv2
import numpy as np

CAMERA_PAGE_WIDTH = 1920
GATE_TILTS = (
    ((0.03, 0.01), (-0.01, 0.03), (-0.03, -0.01), (0.01, -0.03)),
    ((0.05, 0.02), (-0.02, 0.05), (-0.05, -0.02), (0.02, -0.05)),
    ((0.02, 0.05), (-0.05, 0.02), (-0.02, -0.05), (0.05, -0.02)),
)
_detector = cv2.QRCodeDetector()


def decode(image: np.ndarray) -> str | None:
    payload, points, _ = _detector.detectAndDecode(image)
    if not payload or points is None:
        return None
    return payload


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
        if decode(frame) != expected:
            return False
    return True
