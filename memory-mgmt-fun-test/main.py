import sys

x = 10
print(id(x))

y = x
print(id(y))

class Point:
  x = 0
  y = 0

p = Point()
print(p.__dict__)
p.__dict__["x"]=10
p.__dict__["y"]=10
p.__dict__["z"]=10
print(id(p))

print(sys.getrefcount(x))
print(sys.getrefcount(y))
print(sys.getrefcount(p))

print(sys.getsizeof(x))
print(sys.getsizeof(y))
print(sys.getsizeof(p))

class WithSlots():
    __slots__ = ("x", "y")
    def __init__(self):
        self.x = 0
        self.y = 0

s = WithSlots()
print(sys.getrefcount(s))
print(sys.getsizeof(s))

s.__dict__["z"]="should not work"
