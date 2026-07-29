import requests

BASE = "https://httpbin.org"


def get_with_params():
    response = requests.get(f"{BASE}/get", params={"lang": "python", "n": 3}, timeout=10)
    response.raise_for_status()
    return response.json()["args"]


def post_json():
    response = requests.post(f"{BASE}/post", json={"name": "alice", "role": "admin"}, timeout=10)
    return response.json()["json"]


def custom_headers():
    response = requests.get(f"{BASE}/headers", headers={"X-Token": "abc123"}, timeout=10)
    return response.json()["headers"].get("X-Token")


def status_handling():
    response = requests.get(f"{BASE}/status/404", timeout=10)
    return response.status_code, response.ok


def with_session():
    with requests.Session() as session:
        session.headers.update({"X-Session": "shared"})
        first = session.get(f"{BASE}/headers", timeout=10).json()["headers"].get("X-Session")
        second = session.get(f"{BASE}/headers", timeout=10).json()["headers"].get("X-Session")
    return first, second


def main():
    print("get_with_params:", get_with_params())
    print("post_json:", post_json())
    print("custom_headers:", custom_headers())
    print("status_handling:", status_handling())
    print("with_session:", with_session())


if __name__ == "__main__":
    main()
