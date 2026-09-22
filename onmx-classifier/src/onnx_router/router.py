from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import onnxruntime as ort

from onnx_router.paths import MODEL_PATH

ROUTES = {
    "code": "claude-sonnet-5",
    "math": "claude-opus-5",
    "creative": "claude-fable-5-1",
    "general": "claude-haiku-4-5",
}
DEFAULT_MODEL = "claude-haiku-4-5"
THRESHOLD = 0.40


@dataclass(frozen=True)
class Decision:
    prompt: str
    label: str
    confidence: float
    model: str
    fallback: bool
    scores: dict[str, float]

    def to_dict(self) -> dict:
        return asdict(self)


class Router:
    def __init__(self, model_path: Path = MODEL_PATH, threshold: float = THRESHOLD) -> None:
        if not model_path.exists():
            raise FileNotFoundError(f"{model_path.name} not found, run onnx-router-train first")
        self.session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
        meta = self.session.get_modelmeta().custom_metadata_map
        self.classes = meta["classes"].split(",")
        self.threshold = threshold

    def scores(self, prompts: list[str]) -> np.ndarray:
        batch = np.array([[p] for p in prompts], dtype=object)
        _, probabilities = self.session.run(None, {"text": batch})
        return probabilities

    def route(self, prompt: str) -> Decision:
        text = prompt.strip()
        if not text:
            raise ValueError("prompt must not be empty")
        probabilities = self.scores([text])[0]
        best = int(np.argmax(probabilities))
        label = self.classes[best]
        confidence = float(probabilities[best])
        fallback = confidence < self.threshold
        return Decision(
            prompt=text,
            label=label,
            confidence=round(confidence, 4),
            model=DEFAULT_MODEL if fallback else ROUTES[label],
            fallback=fallback,
            scores={
                c: round(float(s), 4) for c, s in zip(self.classes, probabilities, strict=True)
            },
        )
