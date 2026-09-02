import cv2
import numpy as np

import ids
import optics
import page
import qr
import store


class GateFailed(Exception):
    pass


def build(image: np.ndarray) -> dict:
    page_id = ids.mint()

    for attempt, style in enumerate(qr.STYLES, start=1):
        code = qr.render(page_id, image, style["bias"], style["dot"])
        rendered = page.render(code, page_id)
        if optics.passes_gate(rendered, page_id):
            break
    else:
        raise GateFailed(page_id)

    cv2.imwrite(str(store.ORIGINALS / f"{page_id}.png"), image)
    cv2.imwrite(str(store.PAGES / f"{page_id}.png"), rendered)
    store.record(
        page_id,
        {
            "id": page_id,
            "style_attempt": attempt,
            "image_strength": round(1.0 - style["bias"], 2),
            "code_mm": page.CODE_MM,
            "captured": False,
        },
    )
    return store.get(page_id)


def pair(capture: np.ndarray) -> dict:
    found = optics.decode(capture)
    if found is None:
        raise ValueError("no QR code in frame")

    page_id, corners = found
    if not ids.verify(page_id):
        raise ValueError("id signature rejected")
    if store.get(page_id) is None:
        raise ValueError("id is unknown to this server")

    rectified = optics.rectify(capture, corners)
    cv2.imwrite(str(store.CAPTURES / f"{page_id}.png"), rectified)
    store.record(page_id, {"captured": True})
    return store.get(page_id)
