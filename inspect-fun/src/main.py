import inspect


def trace_calls():
    """Print info about the caller and the caller's parent (if any)."""
    frame = inspect.currentframe()
    try:
        caller = frame.f_back
        if caller is None:
            print("No caller frame available")
            return

        print(f"Called from {caller.f_code.co_name} at line {caller.f_lineno}")
        print(f"Local variables: {caller.f_locals}")

        parent = caller.f_back
        if parent is not None:
            print(f"Parent frame: {parent.f_code.co_name} at line {parent.f_lineno}")
            print(f"Parent locals: {parent.f_locals}")
    finally:
        del frame


def outer_function():
    x = 42
    inner_function()


def inner_function():
    y = "hello"
    trace_calls()


if __name__ == "__main__":
    outer_function()