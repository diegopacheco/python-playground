def create_class(name, bases=(), attrs={}):
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return f"{name}({self.value})"
    
    attrs.update({'__init__': __init__, '__str__': __str__})
    return type(name, bases, attrs)

DynamicClass = create_class('DynamicClass')
obj = DynamicClass(42)
print(obj) 