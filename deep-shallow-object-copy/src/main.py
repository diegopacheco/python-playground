import copy

original = {'a': [1, 2, 3], 'b': 4}
shallow = copy.copy(original)
deep = copy.deepcopy(original)

original['a'].append(4)
print(shallow['a'])
print(deep['a'])   