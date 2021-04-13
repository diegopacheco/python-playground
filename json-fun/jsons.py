import json

j =  '{ "name":"John", "age":"30", "city":"New York"}'
y = json.loads(j)

print(y["age"])
print(y)

x = {
  "name": "John",
  "age": 30,
  "city": "New York"
}
# convert into JSON:
z = json.dumps(x)
# the result is a JSON string:
print(z)