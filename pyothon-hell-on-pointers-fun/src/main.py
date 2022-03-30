from pointers import to_ptr, Pointer, decay, malloc, free

a: str = '123'
b: str = 'abc'

@decay
def move(ptr_a: Pointer[str], ptr_b: Pointer[str]):
    ptr_a <<= ptr_b

move(a, b)
print(a, b) # abc abc

memory = malloc(52)
memory <<= "abc"
print(*memory) # abc
free(memory)
#print(*memory) # MemoryError
