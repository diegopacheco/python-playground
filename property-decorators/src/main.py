class Circle:
    def __init__(self, radius):
        self._radius = radius
    
    @property
    def area(self):
        return 3.14159 * self._radius ** 2
    
    @area.setter
    def area(self, value):
        self._radius = (value / 3.14159) ** 0.5

c = Circle(5)
print(c.area) 

c.area = 80
print(c.area)