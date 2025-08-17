from typing import Generic, TypeVar

T = TypeVar('T')

class Container(Generic[T]):
    def __init__(self):
        self._items = []
    
    def add(self, item: T) -> None:
        self._items.append(item)
    
    def get(self, index: int) -> T:
        return self._items[index]
    
    def __class_getitem__(cls, item):
        return type(f"{cls.__name__}[{item.__name__}]", (cls,), {})

IntContainer = Container[int]
StrContainer = Container[str]

int_container = IntContainer()
int_container.add(42)

print(int_container.get(0))
print(int_container.__class__.__name__)