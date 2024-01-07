class Cat:
    def __init__(self):
        self.__count = 0

    def __add__(self, x):
        self.__count += x
        print("We have " + str(self.__count) + " cats now...\n")
    def __sub__(self, x):
        self.__count -= x
        print("OH no! We have " + str(self.__count) + " cats now. \n")

cat = Cat()
cat + 2
cat - 1

