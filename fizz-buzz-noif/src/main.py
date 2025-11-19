from itertools import cycle

def string_mask(a, b):
    return b + a[len(b) :]

def main():
    fizz = cycle(["", "", "Fizz"])
    buzz = cycle(["", "", "", "", "Buzz"])
    numbers = range(1, 101)
    for f, b, n in zip(fizz, buzz, numbers):
        print(string_mask(str(n), f + b))

main()