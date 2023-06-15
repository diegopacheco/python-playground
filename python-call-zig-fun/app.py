import ctypes
lib = ctypes.CDLL("./libadd.so")
print("Zig result is 1 + 2 == " + str(lib.zig_add(1,2)))
