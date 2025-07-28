import pickle

data = {'name': 'Alice', 'scores': [85, 90, 78]}
serialized = pickle.dumps(data)
restored = pickle.loads(serialized)

print(serialized)
print(restored) 