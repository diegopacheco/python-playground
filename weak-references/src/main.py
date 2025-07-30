import weakref

class Node:
    def __init__(self, value):
        self.value = value

node = Node(42)
weak_ref = weakref.ref(node)
print(weak_ref().value)

del node
print(weak_ref())