import copy
import inspect
import pickle

MISSING = sentinel("MISSING")


def resolve(value: int | None | MISSING = MISSING) -> str:
    if value is MISSING:
        return "not provided"
    if value is None:
        return "explicit None"
    return f"value {value}"


def signature() -> str:
    return str(inspect.signature(resolve))


def survives_copy() -> bool:
    return copy.deepcopy(MISSING) is MISSING


def survives_pickle() -> bool:
    return pickle.loads(pickle.dumps(MISSING)) is MISSING


def main() -> None:
    print(f"resolve{signature()}")
    print(f"resolve() -> {resolve()}")
    print(f"resolve(None) -> {resolve(None)}")
    print(f"resolve(7) -> {resolve(7)}")
    print(f"identity kept after copy={survives_copy()} pickle={survives_pickle()}")


if __name__ == "__main__":
    main()
