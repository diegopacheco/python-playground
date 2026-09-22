import numpy as np
import pytest
from sklearn.pipeline import Pipeline

from onnx_router.dataset import texts_and_labels
from onnx_router.router import DEFAULT_MODEL, ROUTES, Router

UNSEEN = [
    ("write a java method that removes duplicates from a list", "code"),
    ("why does my python script raise a key error", "code"),
    ("what is the derivative of cos x", "math"),
    ("calculate the area of a triangle with base 6 and height 4", "math"),
    ("write a poem about a rainy morning", "creative"),
    ("tell me a story about a dragon who is afraid of fire", "creative"),
    ("what is the capital of japan", "general"),
    ("how do I make a cup of coffee", "general"),
]


def test_onnx_scores_match_sklearn_so_the_exported_model_is_the_trained_model(
    pipeline: Pipeline, router: Router
) -> None:
    texts = texts_and_labels()[0] + [text for text, _ in UNSEEN]
    expected = pipeline.predict_proba(texts)
    order = [list(pipeline.classes_).index(c) for c in router.classes]
    np.testing.assert_allclose(router.scores(texts), expected[:, order], atol=1e-4)


@pytest.mark.parametrize(("prompt", "label"), UNSEEN)
def test_unseen_prompts_reach_the_model_owning_their_category(
    router: Router, prompt: str, label: str
) -> None:
    decision = router.route(prompt)
    assert decision.label == label
    assert decision.model == ROUTES[label]
    assert not decision.fallback


def test_prompt_with_no_known_signal_falls_back_to_the_cheap_default(router: Router) -> None:
    decision = router.route("banana")
    assert decision.fallback
    assert decision.confidence < router.threshold
    assert decision.model == DEFAULT_MODEL


def test_scores_form_a_distribution_over_every_route(router: Router) -> None:
    decision = router.route("solve x + 1 = 3")
    assert set(decision.scores) == set(ROUTES)
    assert sum(decision.scores.values()) == pytest.approx(1.0, abs=1e-3)


def test_empty_prompt_is_rejected_instead_of_routed(router: Router) -> None:
    with pytest.raises(ValueError):
        router.route("   ")
