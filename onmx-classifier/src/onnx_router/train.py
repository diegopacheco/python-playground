from pathlib import Path

from skl2onnx import to_onnx
from skl2onnx.common.data_types import StringTensorType
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from onnx_router.dataset import texts_and_labels
from onnx_router.paths import MODEL_PATH


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(lowercase=True, ngram_range=(1, 2), token_pattern=r"\b\w+\b"),
            ),
            ("clf", LogisticRegression(C=100.0, max_iter=1000)),
        ]
    )


def train() -> Pipeline:
    texts, labels = texts_and_labels()
    pipeline = build_pipeline()
    pipeline.fit(texts, labels)
    return pipeline


def export(pipeline: Pipeline, path: Path) -> Path:
    onnx_model = to_onnx(
        pipeline,
        initial_types=[("text", StringTensorType([None, 1]))],
        options={LogisticRegression: {"zipmap": False}},
        target_opset={"": 17, "ai.onnx.ml": 3},
    )
    entry = onnx_model.metadata_props.add()
    entry.key = "classes"
    entry.value = ",".join(pipeline.classes_)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(onnx_model.SerializeToString())
    return path


def main() -> None:
    path = export(train(), MODEL_PATH)
    print(f"model written to {path.relative_to(path.parents[1])}")


if __name__ == "__main__":
    main()
