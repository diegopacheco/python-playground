from functools import partial

multiply = lambda x, y: x * y
double = partial(multiply, 2)
print(double(5))