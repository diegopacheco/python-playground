class InfiniteRange:
    def __init__(self, start=0):
        self.start = start
    
    def __getitem__(self, key):
        if isinstance(key, slice):
            return [self.start + i for i in range(key.start or 0, key.stop, key.step or 1)]
        return self.start + key
    
    def __contains__(self, value):
        return value >= self.start

inf = InfiniteRange(5)
print(inf[10])
print(inf[0:5])
print(100 in inf)