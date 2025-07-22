class Version:
    def __init__(self, version_string):
        self.version = tuple(map(int, version_string.split('.')))
    
    def __lt__(self, other):
        return self.version < other.version

v1 = Version("1.2.3")
v2 = Version("1.3.0")

# It will print True
print(v1 < v2)
print(v1.version)
print(v2.version)