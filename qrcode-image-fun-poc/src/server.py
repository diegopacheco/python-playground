import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

import pipeline
import store

MAX_BYTES = 12 * 1024 * 1024

app = FastAPI(title="qrcode-image-fun-poc")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


async def _decode_upload(upload: UploadFile) -> np.ndarray:
    raw = await upload.read()
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, "image too large")
    image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(415, "not a decodable image")
    return image


@app.post("/uploads")
async def upload(image: UploadFile = File(...)) -> dict:
    try:
        return pipeline.build(await _decode_upload(image))
    except pipeline.GateFailed:
        raise HTTPException(422, "no styling survived the verification gate")


@app.post("/captures")
async def capture(frame: UploadFile = File(...)) -> dict:
    try:
        return pipeline.pair(await _decode_upload(frame))
    except ValueError as bad:
        raise HTTPException(422, str(bad))


@app.get("/pairs")
def pairs() -> list:
    return sorted(store.all_pairs().values(), key=lambda entry: entry["id"])


@app.get("/pairs/{page_id}")
def one_pair(page_id: str) -> dict:
    entry = store.get(page_id)
    if entry is None:
        raise HTTPException(404, "unknown id")
    return entry


def _serve(folder, page_id: str) -> FileResponse:
    path = folder / f"{page_id}.png"
    if not path.exists():
        raise HTTPException(404, "not found")
    return FileResponse(path, media_type="image/png")


@app.get("/pages/{page_id}.png")
def page_png(page_id: str) -> FileResponse:
    return _serve(store.PAGES, page_id)


@app.get("/originals/{page_id}.png")
def original_png(page_id: str) -> FileResponse:
    return _serve(store.ORIGINALS, page_id)


@app.get("/captures/{page_id}.png")
def capture_png(page_id: str) -> FileResponse:
    return _serve(store.CAPTURES, page_id)
