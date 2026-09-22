import pytest
from sklearn.pipeline import Pipeline

from onnx_router.router import Router
from onnx_router.train import export, train


@pytest.fixture(scope="session")
def pipeline() -> Pipeline:
    return train()


@pytest.fixture(scope="session")
def router(pipeline: Pipeline, tmp_path_factory: pytest.TempPathFactory) -> Router:
    path = export(pipeline, tmp_path_factory.mktemp("models") / "router.onnx")
    return Router(path)
