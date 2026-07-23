from typing import Dict, Generic, List, NewType, Optional, Protocol, TypedDict, TypeVar

UserId = NewType("UserId", int)

T = TypeVar("T")


class User(TypedDict):
    id: int
    name: str
    email: str


class Comparable(Protocol):
    def __lt__(self, other: "Comparable") -> bool:
        ...


class Stack(Generic[T]):
    def __init__(self) -> None:
        self._items: List[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        return self._items.pop()

    def size(self) -> int:
        return len(self._items)


def greet(name: str, times: int = 1) -> str:
    return " ".join([f"hi {name}"] * times)


def find_user(users: List[User], user_id: UserId) -> Optional[User]:
    for user in users:
        if user["id"] == int(user_id):
            return user
    return None


def total_prices(cart: Dict[str, float]) -> float:
    return sum(cart.values())


def smallest(values: List[Comparable]) -> Comparable:
    result = values[0]
    for value in values[1:]:
        if value < result:
            result = value
    return result


def main() -> None:
    print("greet:", greet("alice", 2))

    stack: Stack[int] = Stack()
    stack.push(1)
    stack.push(2)
    print("stack pop:", stack.pop(), "size:", stack.size())

    users: List[User] = [
        {"id": 1, "name": "alice", "email": "a@x.com"},
        {"id": 2, "name": "bob", "email": "b@x.com"},
    ]
    print("find_user:", find_user(users, UserId(2)))

    print("total_prices:", total_prices({"a": 1.5, "b": 2.5}))
    print("smallest:", smallest([5, 3, 9, 1, 7]))


if __name__ == "__main__":
    main()
