numbers = [2, 4, 6, 8]
print(all(x % 2 == 0 for x in numbers))
print(any(x > 5 for x in numbers))  