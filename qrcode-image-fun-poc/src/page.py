import cv2
import numpy as np

import qr

DPI = 300
MM = DPI / 25.4
PAGE_W = int(round(210 * MM))
PAGE_H = int(round(297 * MM))
MARGIN = int(round(18 * MM))
RULE_GAP = int(round(8 * MM))
CODE_MM = 25
CODE_SIDE = qr.CODE_PX
CODE_X = (PAGE_W - CODE_SIDE) // 2
CODE_Y = PAGE_H - MARGIN - CODE_SIDE

CODE_CORNERS = np.array(
    [
        [CODE_X, CODE_Y],
        [CODE_X + CODE_SIDE, CODE_Y],
        [CODE_X + CODE_SIDE, CODE_Y + CODE_SIDE],
        [CODE_X, CODE_Y + CODE_SIDE],
    ],
    dtype=np.float32,
)


def render(code: np.ndarray, page_id: str) -> np.ndarray:
    page = np.full((PAGE_H, PAGE_W, 3), 255, np.uint8)

    for y in range(MARGIN + RULE_GAP * 2, CODE_Y - RULE_GAP * 2, RULE_GAP):
        cv2.line(page, (MARGIN, y), (PAGE_W - MARGIN, y), (222, 222, 222), 2)

    cv2.line(page, (MARGIN, MARGIN), (PAGE_W - MARGIN, MARGIN), (40, 40, 40), 4)
    cv2.putText(
        page,
        page_id,
        (CODE_X, CODE_Y - int(6 * MM)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (120, 120, 120),
        2,
        cv2.LINE_AA,
    )

    page[CODE_Y : CODE_Y + CODE_SIDE, CODE_X : CODE_X + CODE_SIDE] = code
    return page
