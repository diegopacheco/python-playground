import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any

import build_info
import comprehension_unpacking
import frozendict_type
import profiling_sampling
import profiling_tracing
import sentinel_type
import typeddict_closed
import typeddict_extra_items
import typeform

SRC = Path(__file__).resolve().parent.parent / "src"


def run_feature(name: str) -> list[str]:
    result = subprocess.run(
        [sys.executable, str(SRC / f"{name}.py")],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.splitlines()


class LazyImportsTest(unittest.TestCase):
    def test_lazy_keyword_defers_loading_until_first_runtime_use(self) -> None:
        lines = run_feature("lazy_imports")
        self.assertEqual(lines[0], "before use: loaded=False pending=True")
        self.assertEqual(lines[2], "after use: loaded=True pending=False")

    def test_lazy_modules_global_defers_only_the_listed_module(self) -> None:
        lines = run_feature("lazy_modules_global")
        self.assertEqual(lines[0], "before use: {'decimal': False, 'fractions': True}")
        self.assertEqual(lines[2], "after use: {'decimal': True, 'fractions': True}")

    def test_flag_and_env_var_make_plain_imports_lazy(self) -> None:
        lines = run_feature("lazy_imports_flag")
        self.assertEqual(lines[0], "default: normal True")
        self.assertEqual(lines[1], "-X lazy_imports=all: all False")
        self.assertEqual(lines[2], "PYTHON_LAZY_IMPORTS=all: all False")


class ProfilingTest(unittest.TestCase):
    def test_tracing_profiler_counts_every_call_exactly(self) -> None:
        self.assertEqual(profiling_tracing.call_count(10), 177)

    def test_sampling_workload_counts_each_element_per_molecule(self) -> None:
        counts = profiling_sampling.count_elements(profiling_sampling.molecules(10))
        self.assertEqual(counts, {"C": 10, "H": 20, "O": 10, "N": 10})


class TypedDictTest(unittest.TestCase):
    def test_closed_typeddict_is_marked_closed_so_values_are_ints(self) -> None:
        self.assertTrue(typeddict_closed.Point2D.__closed__)
        self.assertEqual(typeddict_closed.total(typeddict_closed.Point2D(x=3, y=4)), 7)

    def test_extra_items_accepts_additional_int_dimensions(self) -> None:
        point = typeddict_extra_items.Point(x=3, y=4, z=5, w=6)
        self.assertIs(typeddict_extra_items.Point.__extra_items__, int)
        self.assertEqual(typeddict_extra_items.total(point), 18)


class TypeFormTest(unittest.TestCase):
    def test_trycast_returns_value_only_when_it_matches_the_type_form(self) -> None:
        self.assertEqual(typeform.trycast(str | None, "hi"), "hi")
        self.assertEqual(typeform.trycast(int | float, 2.5), 2.5)
        self.assertIsNone(typeform.trycast(int, "hi"))


class SentinelTest(unittest.TestCase):
    def test_sentinel_separates_missing_argument_from_none(self) -> None:
        self.assertEqual(sentinel_type.resolve(), "not provided")
        self.assertEqual(sentinel_type.resolve(None), "explicit None")
        self.assertEqual(sentinel_type.resolve(0), "value 0")

    def test_sentinel_shows_its_name_in_the_signature(self) -> None:
        self.assertEqual(sentinel_type.signature(), "(value: int | None | MISSING = MISSING) -> str")

    def test_sentinel_identity_survives_copy_and_pickle(self) -> None:
        self.assertTrue(sentinel_type.survives_copy())
        self.assertTrue(sentinel_type.survives_pickle())


class FrozenDictTest(unittest.TestCase):
    def test_override_returns_new_mapping_and_keeps_the_original(self) -> None:
        tuned = frozendict_type.override(frozendict_type.DEFAULTS, timeout=5)
        self.assertEqual(tuned, {"retries": 3, "timeout": 5})
        self.assertEqual(frozendict_type.DEFAULTS, {"retries": 3, "timeout": 30})

    def test_frozendict_rejects_mutation(self) -> None:
        self.assertTrue(frozendict_type.is_immutable(frozendict_type.DEFAULTS))
        config: Any = frozendict_type.DEFAULTS
        with self.assertRaises(TypeError):
            config["retries"] = 1

    def test_equal_frozendicts_hash_alike_so_they_work_as_keys(self) -> None:
        same = frozendict(timeout=30, retries=3)
        self.assertEqual(frozendict_type.usage([frozendict_type.DEFAULTS, same])[same], 2)


class ComprehensionUnpackingTest(unittest.TestCase):
    def test_star_flattens_and_double_star_merges_with_last_key_winning(self) -> None:
        rows = [[1, 2], [2, 3], []]
        self.assertEqual(comprehension_unpacking.flatten(rows), [1, 2, 2, 3])
        self.assertEqual(comprehension_unpacking.unique(rows), {1, 2, 3})
        self.assertEqual(list(comprehension_unpacking.stream(rows)), [1, 2, 2, 3])
        self.assertEqual(comprehension_unpacking.merge([{"a": 1}, {"b": 2}, {"a": 3}]), {"a": 3, "b": 2})


class BuildInfoTest(unittest.TestCase):
    def test_interpreter_is_python_3_15_built_with_clang(self) -> None:
        info = build_info.build_info()
        self.assertTrue(info.version.startswith("3.15."))
        self.assertIn("Clang", info.compiler)


if __name__ == "__main__":
    unittest.main()
