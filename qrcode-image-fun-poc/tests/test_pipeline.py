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
        drowned = qr.render(payload, sample_image(), field=0.0, dot=0.02)
        self.assertFalse(optics.passes_gate(page.render(drowned, payload), payload))


class OnePhotographCarriesTheIdentity(unittest.TestCase):
    def test_a_tilted_photograph_yields_the_id_that_pairs(self):
        entry = pipeline.build(sample_image())
        rendered = cv2.imread(str(pipeline.store.PAGES / f"{entry['id']}.png"))

        scanned = optics.decode(photograph(rendered))
        self.assertEqual(scanned, entry["id"])

        paired = pipeline.pair(scanned)
        self.assertEqual(paired["id"], entry["id"])
        self.assertTrue(paired["captured"])

    def test_an_angle_outside_the_gate_never_yields_another_page(self):
        entry = pipeline.build(sample_image())
        rendered = cv2.imread(str(pipeline.store.PAGES / f"{entry['id']}.png"))
        scanned = optics.decode(photograph_from_a_bad_angle(rendered))
        if scanned is None:
            return
        self.assertEqual(scanned, entry["id"])

    def test_a_frame_with_no_code_yields_no_id(self):
        self.assertIsNone(optics.decode(np.full((900, 700, 3), 255, np.uint8)))


class OnlyTheServersOwnIdsPair(unittest.TestCase):
    def test_a_forged_id_never_reaches_the_store(self):
        forged = "ZZZZZZZZZZZZZZZZZZZZ" + "YYYYYYYYYYYYYYYY"
        with self.assertRaises(ValueError):
            pipeline.pair(forged)

    def test_a_signed_id_this_server_never_minted_is_refused(self):
        with self.assertRaises(ValueError):
            pipeline.pair(ids.mint())


if __name__ == "__main__":
    unittest.main(verbosity=2)
