class Animal:
    def __init__(self, name, legs):
        self.name = name
        self.legs = legs

    def describe(self):
        return f"{self.name} has {self.legs} legs"


class Dog(Animal):
    def __init__(self, name):
        super().__init__(name, 4)

    def sound(self):
        return "woof"


def for_loop():
    total = 0
    for i in range(1, 6):
        total += i
    return total


def while_loop():
    n = 10
    steps = 0
    while n > 1:
        n = n // 2
        steps += 1
    return steps


def loop_over_collection():
    fruits = ["apple", "banana", "cherry"]
    return [f"{i}:{fruit}" for i, fruit in enumerate(fruits)]


def lambdas():
    square = lambda x: x * x
    add = lambda a, b: a + b
    return square(5), add(3, 4)


def sorting():
    people = [("alice", 30), ("bob", 25), ("carol", 35)]
    by_age = sorted(people, key=lambda p: p[1])
    by_name_desc = sorted(people, key=lambda p: p[0], reverse=True)
    return by_age, by_name_desc


def main():
    print("for_loop sum 1..5:", for_loop())
    print("while_loop halving steps:", while_loop())
    print("loop_over_collection:", loop_over_collection())
    print("lambdas:", lambdas())
    by_age, by_name_desc = sorting()
    print("sorted by age:", by_age)
    print("sorted by name desc:", by_name_desc)

    dog = Dog("Rex")
    print("class describe:", dog.describe())
    print("class method:", dog.sound())
    print("isinstance Animal:", isinstance(dog, Animal))


if __name__ == "__main__":
    main()
