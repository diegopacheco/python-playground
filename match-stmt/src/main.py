def handle_response(status):
    match status:
        case 200:
            return "Success"
        case 404 | 403:
            return "Not found or forbidden"
        case code if 400 <= code < 500:
            return "Client error"
        case _:
            return "Unknown status"

if __name__ == "__main__":
    print(handle_response(200))  # Output: Success
    print(handle_response(404))  # Output: Not found or forbidden
    print(handle_response(403))  # Output: Not found or forbidden
    print(handle_response(500))  # Output: Unknown status
    print(handle_response(400))  # Output: Client error
    print(handle_response(401))  # Output: Client error