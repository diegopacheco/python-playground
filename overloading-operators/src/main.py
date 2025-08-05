class Vector:
    def __init__(self, *components):
        self.components = components
    
    def __matmul__(self, other):  # @ operator
        return sum(a * b for a, b in zip(self.components, other.components))
    
    def __rshift__(self, n):  # >> operator
        return Vector(*self.components[n:], *self.components[:n])

    def __repr__(self):
        return f"Vector{self.components}"

v1 = Vector(1, 2, 3)
v2 = Vector(4, 5, 6)
print(v1 @ v2)
print(v1 >> 1)    