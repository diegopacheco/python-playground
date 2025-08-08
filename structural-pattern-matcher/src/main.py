def process_data(data):
    match data:
        case {'type': 'user', 'name': str(name)} if len(name) > 5:
            return f"Long name user: {name}"
        case {'type': 'user', 'name': str(name)}:
            return f"Short name user: {name}"
        case _:
            return "Unknown data"

print(process_data({'type': 'user', 'name': 'Alexander'}))
print(process_data({'type': 'user', 'name': 'Alex'}))