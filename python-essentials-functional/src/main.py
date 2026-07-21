from functools import reduce, partial


def map_filter_reduce():
    numbers = [1, 2, 3, 4, 5, 6]
    doubled = list(map(lambda x: x * 2, numbers))
    evens = list(filter(lambda x: x % 2 == 0, numbers))
    total = reduce(lambda acc, x: acc + x, numbers, 0)
    return doubled, evens, total


def make_counter():
    count = 0

    def increment():
        nonlocal count
        count += 1
        return count

    return increment


def multiplier(factor):
    return lambda x: x * factor


def partials():
    def power(base, exponent):
        return base ** exponent

    square = partial(power, exponent=2)
    cube = partial(power, exponent=3)
    return square(5), cube(2)


def compose(*functions):
    def composed(value):
        for func in reversed(functions):
            value = func(value)
        return value

    return composed


def main():
    print("map_filter_reduce:", map_filter_reduce())

    counter = make_counter()
    print("closure counter:", counter(), counter(), counter())

    triple = multiplier(3)
    print("closure multiplier:", triple(10))

    print("partials:", partials())

    pipeline = compose(lambda x: x + 1, lambda x: x * 2)
    print("compose (x*2)+1 of 5:", pipeline(5))


if __name__ == "__main__":
    main()
