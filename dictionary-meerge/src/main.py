dict1 = {'a': 1, 'b': 2}
dict2 = {'c': 3, 'd': 4}
merged = dict1 | dict2

print("dict1: ", dict1)
print("dict2: ", dict2)
print("merged: ", merged)

dict1 |= dict2
print("dict1 with merge in place: ", dict1)