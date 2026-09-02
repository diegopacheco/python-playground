import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ.setdefault("QRPOC_DATA", tempfile.mkdtemp(prefix="qrpoc-"))

import cv2
import numpy as np

import ids
import optics
import page
import pipeline
import qr


def sample_image() -> np.ndarray:
    rng = np.random.default_rng(3)
    canvas = np.zeros((600, 600, 3), np.uint8)
    for _ in range(40):
        centre = tuple(int(v) for v in rng.integers(0, 600, 2))
        colour = tuple(int(v) for v in rng.integers(0, 255, 3))
        cv2.circle(canvas, centre, int(rng.integers(30, 160)), colour, -1)
    return canvas


def photograph(rendered: np.ndarray) -> np.ndarray:
    frame = optics.simulate_camera(rendered)
    return cv2.GaussianBlur(optics.tilt(frame, optics.GATE_TILTS[1]), (3, 3), 0)


def photograph_from_a_bad_angle(rendered: np.ndarray) -> np.ndarray:
    frame = optics.simulate_camera(rendered)
    height, width = frame.shape[:2]
    flat = np.float32([[0, 0], [width, 0], [width, height], [0, height]])
    steep = np.float32(
        [[60, 25], [width - 15, 70], [width - 70, height - 30], [20, height - 90]]
    )
    warped = cv2.warpPerspective(
        frame,
        cv2.getPerspectiveTransform(flat, steep),
        (width, height),
        borderValue=(235, 235, 235),
    )
    return cv2.GaussianBlur(warped, (3, 3), 0)


def module_grid(image: np.ndarray, scale: float) -> np.ndarray:
    left = int(page.CODE_X * scale)
    top = int(page.CODE_Y * scale)
    side = int(page.CODE_SIDE * scale)
    patch = image[top : top + side, left : left + side]
    grey = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
    shrunk = cv2.resize(grey, (qr.MODULES, qr.MODULES), interpolation=cv2.INTER_AREA)
    return shrunk < shrunk.mean()


def module_agreement(rectified: np.ndarray, printed: np.ndarray) -> float:
    captured = module_grid(rectified, optics.RECTIFIED_SCALE)
    truth = module_grid(printed, 1.0)
    return float((captured == truth).mean())


class IdentityIsUnforgeable(unittest.TestCase):
    def test_a_minted_id_verifies(self):
        self.assertTrue(ids.verify(ids.mint()))

    def test_a_tampered_id_is_rejected(self):
        minted = ids.mint()
        flipped = "A" if minted[0] != "A" else "B"
        self.assertFalse(ids.verify(flipped + minted[1:]))

    def test_a_well_formed_but_unsigned_id_is_rejected(self):
        self.assertFalse(ids.verify("A" * len(ids.mint())))


class TheGateStopsUnreadableStyling(unittest.TestCase):
    def test_the_chosen_styling_survives_a_simulated_camera(self):
        entry = pipeline.build(sample_image())
        rendered = cv2.imread(str(pipeline.store.PAGES / f"{entry['id']}.png"))
        self.assertTrue(optics.passes_gate(rendered, entry["id"]))

    def test_the_gate_can_actually_fail(self):
        payload = ids.mint()
        drowned = qr.render(payload, sample_image(), bias=0.0, dot=0.02)
        self.assertFalse(optics.passes_gate(page.render(drowned, payload), payload))


class OneFrameCarriesIdentityAndPage(unittest.TestCase):
    def test_a_tilted_photograph_pairs_and_rectifies(self):
        entry = pipeline.build(sample_image())
        rendered = cv2.imread(str(pipeline.store.PAGES / f"{entry['id']}.png"))

        paired = pipeline.pair(photograph(rendered))
        self.assertEqual(paired["id"], entry["id"])
        self.assertTrue(paired["captured"])

        rectified = cv2.imread(str(pipeline.store.CAPTURES / f"{entry['id']}.png"))
        self.assertEqual(
            rectified.shape[:2],
            (
                int(page.PAGE_H * optics.RECTIFIED_SCALE),
                int(page.PAGE_W * optics.RECTIFIED_SCALE),
            ),
        )
        self.assertGreater(module_agreement(rectified, rendered), 0.9)

    def test_an_angle_outside_the_gate_never_pairs_the_wrong_page(self):
        entry = pipeline.build(sample_image())
        rendered = cv2.imread(str(pipeline.store.PAGES / f"{entry['id']}.png"))
        try:
            paired = pipeline.pair(photograph_from_a_bad_angle(rendered))
        except ValueError:
            return
        self.assertEqual(paired["id"], entry["id"])

    def test_a_frame_with_no_code_is_refused(self):
        with self.assertRaises(ValueError):
            pipeline.pair(np.full((900, 700, 3), 255, np.uint8))

    def test_a_forged_id_never_reaches_the_store(self):
        forged = "ZZZZZZZZZZZZZZZZZZZZ" + "YYYYYYYYYYYYYYYY"
        rendered = page.render(qr.render(forged, sample_image(), 1.0, 0.5), forged)
        with self.assertRaises(ValueError):
            pipeline.pair(optics.simulate_camera(rendered))


if __name__ == "__main__":
    unittest.main(verbosity=2)
