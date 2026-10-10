from collections import Counter

type Config = frozendict[str, int]

DEFAULTS: Config = frozendict(retries=3, timeout=30)


def override(config: Config, **changes: int) -> Config:
    return config | changes


def is_immutable(config: Config) -> bool:
    return not hasattr(config, "__setitem__")


def usage(configs: list[Config]) -> Counter[Config]:
    return Counter(configs)


def main() -> None:
    tuned = override(DEFAULTS, timeout=5)
    print(f"defaults={DEFAULTS}")
    print(f"tuned={tuned}")
    print(f"immutable={is_immutable(DEFAULTS)}")
    print(f"usage={usage([DEFAULTS, tuned, frozendict(retries=3, timeout=30)])}")


if __name__ == "__main__":
    main()
