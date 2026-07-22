from collections import Counter, defaultdict, namedtuple
from itertools import chain, groupby, accumulate


def for_else():
    for n in [3, 5, 7, 9]:
        if n % 2 == 0:
            break
    else:
        return "no even number found"
    return "found even"


def walrus():
    values = [1, 2, 3, 4, 5, 6]
    return [y for x in values if (y := x * x) > 10]


def dict_merge():
    defaults = {"color": "black", "size": "m"}
    overrides = {"size": "l", "material": "cotton"}
    return defaults | overrides


def fstring_debug():
    width = 4
    height = 5
    return f"{width=} {height=} {width * height=}"


def collections_tools():
    counts = Counter("mississippi")
    grouped = defaultdict(list)
    for word in ["ant", "bear", "cat", "bee"]:
        grouped[len(word)].append(word)
    Point = namedtuple("Point", ["x", "y"])
    p = Point(3, 4)
    return counts.most_common(2), dict(grouped), (p.x, p.y)


def itertools_tools():
    flattened = list(chain([1, 2], [3, 4], [5]))
    running = list(accumulate([1, 2, 3, 4]))
    keyed = {k: list(g) for k, g in groupby("aaabbbcca")}
    return flattened, running, keyed


def main():
    print("for_else:", for_else())
    print("walrus:", walrus())
    print("dict_merge:", dict_merge())
    print("fstring_debug:", fstring_debug())
    print("collections_tools:", collections_tools())
    print("itertools_tools:", itertools_tools())


if __name__ == "__main__":
    main()
