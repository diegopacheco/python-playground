age = 29
status = "adult" if age >= 21 else "minor"
print(f"you are {status}")

for i in range(1, 6):
    print(i)

for index, value in enumerate(["a", "b", "c"]):
    print(f"index: {index} value: {value}")

evens = [x for x in range(10) if x % 2 == 0]
print(f"even numbers 0 to 9 {evens}")
