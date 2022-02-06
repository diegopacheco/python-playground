mytuple = ("apple", "banana", "cherry")
myit = iter(mytuple)

print(next(myit))
print(next(myit))
print(next(myit))

try:
    print(next(myit))
except StopIteration:
  print("StopIteration error")
