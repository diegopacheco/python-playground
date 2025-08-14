def dynamic_function_creator(func_name, operation):
    def template(x, y):
        return operation(x, y)
    
    globals()[func_name] = template
    locals()[f"local_{func_name}"] = template

dynamic_function_creator('add_func', lambda x, y: x + y)
dynamic_function_creator('mul_func', lambda x, y: x * y)

print(add_func(5, 3))
print(mul_func(4, 6)) 