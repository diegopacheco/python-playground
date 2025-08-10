import dis

def sample_function(x, y):
    return x + y * 2

dis.dis(sample_function)
instructions = list(dis.get_instructions(sample_function))
print(f"Function has {len(instructions)} instructions")