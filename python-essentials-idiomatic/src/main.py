def comprehensions():
    squares = [x * x for x in range(6)]
    evens = {x for x in range(10) if x % 2 == 0}
    lookup = {c: ord(c) for c in "abc"}
    return squares, evens, lookup


def enumerate_and_zip():
    names = ["alice", "bob"]
    ages = [30, 25]
    paired = list(zip(names, ages))
    indexed = [(i, n) for i, n in enumerate(names, start=1)]
    return paired, indexed


def unpacking():
    first, *rest = [1, 2, 3, 4]
    a, b = 10, 20
    a, b = b, a
    return first, rest, (a, b)


def dict_get_and_setdefault():
    counts = {}
    for ch in "banana":
        counts[ch] = counts.get(ch, 0) + 1
    groups = {}
    for word in ["ant", "bee", "ape"]:
        groups.setdefault(word[0], []).append(word)
    return counts, groups


def eafp():
    data = {"value": "42"}
    try:
        number = int(data["value"])
    except (KeyError, ValueError):
        number = 0
    return number


def string_join_and_ternary():
    words = ["python", "is", "fun"]
    sentence = " ".join(words)
    label = "even" if len(words) % 2 == 0 else "odd"
    return sentence, label


def main():
    print("comprehensions:", comprehensions())
    print("enumerate_and_zip:", enumerate_and_zip())
    print("unpacking:", unpacking())
    print("dict_get_and_setdefault:", dict_get_and_setdefault())
    print("eafp:", eafp())
    print("string_join_and_ternary:", string_join_and_ternary())


if __name__ == "__main__":
    main()
