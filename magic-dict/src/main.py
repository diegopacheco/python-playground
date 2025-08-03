class MagicDict:
    def __init__(self):
        self._data = {}
    
    def __missing__(self, key):
        return f"Missing: {key}"
    
    def __bool__(self):
        return len(self._data) > 0
    
    def __getitem__(self, key):
        return self._data.get(key, self.__missing__(key))

md = MagicDict()
print(md['nonexistent'])
print(bool(md)) 