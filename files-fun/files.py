f = open("demofile.txt", "r")
print(f.read())
f.close()

f = open("demofile.txt", "r")
for x in f:
  print(x)
f.close()
