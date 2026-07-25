import json
from datetime import datetime


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def dumps_and_loads():
    person = {"name": "alice", "age": 30, "roles": ["admin", "user"], "active": True}
    text = json.dumps(person)
    back = json.loads(text)
    return text, back


def pretty_print():
    data = {"b": 2, "a": 1, "nested": {"y": 20, "x": 10}}
    return json.dumps(data, indent=2, sort_keys=True)


def custom_encoder():
    event = {"name": "login", "at": datetime(2026, 7, 12, 9, 30, 0)}
    return json.dumps(event, cls=DateTimeEncoder)


def parse_numbers():
    text = '{"count": 42, "ratio": 3.14, "items": [1, 2, 3]}'
    parsed = json.loads(text)
    return type(parsed["count"]).__name__, type(parsed["ratio"]).__name__, parsed["items"]


def main():
    text, back = dumps_and_loads()
    print("dumps:", text)
    print("loads:", back)
    print("pretty_print:")
    print(pretty_print())
    print("custom_encoder:", custom_encoder())
    print("parse_numbers:", parse_numbers())


if __name__ == "__main__":
    main()
