res = sorted([1, 2, 3, 4, 5, 6], reverse=True)
print(res)

rev = res[::-1]
print(rev)

squares = [x**2 for x in range(5)]
print(f"original: {[0, 1, 2, 3, 4]} squares: {squares}")
