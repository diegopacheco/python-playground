import build_info
import comprehension_unpacking
import frozendict_type
import lazy_imports
import lazy_imports_flag
import lazy_modules_global
import profiling_tracing
import sentinel_type
import typeddict_closed
import typeddict_extra_items
import typeform

FEATURES = (
    lazy_imports,
    lazy_modules_global,
    lazy_imports_flag,
    profiling_tracing,
    typeddict_closed,
    typeddict_extra_items,
    typeform,
    sentinel_type,
    frozendict_type,
    comprehension_unpacking,
    build_info,
)


def main() -> None:
    for feature in FEATURES:
        print(f"\n== {feature.__name__}")
        feature.main()
    print("\n== profiling_sampling")
    print("not run here: Tachyon needs elevated permissions, run ./scripts/flamegraph.sh")


if __name__ == "__main__":
    main()
