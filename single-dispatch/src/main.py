from functools import singledispatch

@singledispatch
def process(arg):
    print(f"Processing {arg}")

@process.register
def _(arg: int):
    print(f"Processing integer: {arg * 2}")

@process.register
def _(arg: list):
    print(f"Processing list with {len(arg)} items")

process("hello")
process(5)
process([1, 2, 3])