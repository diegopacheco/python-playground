from functools import lru_cache, cache

@lru_cache(maxsize=128)
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

@cache  # Unlimited cache (Python 3.9+)
def expensive_function(x, y):
    return x ** y + y ** x

if __name__ == "__main__":
    print("Fibonacci of 12:", fibonacci(12))
    print("Fibonacci of 12:", fibonacci(12))
    print("Expensive function (2, 3):", expensive_function(2, 3))
    print("Expensive function (3, 2):", expensive_function(3, 2))
    print("Expensive function (4, 5):", expensive_function(4, 5))