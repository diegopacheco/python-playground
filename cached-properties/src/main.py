from functools import cached_property

class DataProcessor:
    def __init__(self, data):
        self.data = data
    
    @cached_property
    def expensive_calculation(self):
        print("Performing expensive calculation...")
        return sum(x ** 2 for x in self.data)

dp = DataProcessor([1, 2, 3, 4, 5])
print(dp.expensive_calculation)
print(dp.expensive_calculation)
print(dp.expensive_calculation)