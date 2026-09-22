import pytest

from library import stats


def test_total_pages_sums_every_book() -> None:
    assert stats.total_pages([100, 250, 50]) == 400


def test_average_price_of_empty_library_is_zero_not_division_error() -> None:
    assert stats.average_price([]) == 0.0


def test_average_price_is_rounded_to_cents() -> None:
    assert stats.average_price([10.0, 10.0, 10.01]) == 10.0


def test_most_expensive_keeps_first_on_tie() -> None:
    assert stats.most_expensive(["a", "b"], [5.0, 5.0]) == "a"


def test_most_expensive_rejects_misaligned_lists() -> None:
    with pytest.raises(ValueError):
        stats.most_expensive(["a"], [1.0, 2.0])


def test_compiled_function_rejects_wrong_types_at_runtime() -> None:
    if stats.__file__ is None or stats.__file__.endswith(".py"):
        pytest.skip("stats is not compiled by mypyc")
    with pytest.raises(TypeError):
        stats.total_pages("not a list")  # type: ignore[arg-type]
