from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "models" / "router.onnx"
STATIC_DIR = Path(__file__).resolve().parent / "static"
