if (n := len(data := input("Enter data: "))) > 5:
    print(f"Long data: {data}")
else:
    print(f"Data '{data}' has length {n}, which is not > 5")
    print(f"Try entering more than 5 characters to see the 'Long data' message")