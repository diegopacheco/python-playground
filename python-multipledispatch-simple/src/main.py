from multipledispatch import dispatch

@dispatch(int, int)
def add(x, y):
    return x + y

@dispatch(object, object)
def add(x, y):
    return "%s + %s" % (x, y)

print(add(1, 2))
print(add(1, 'hello'))