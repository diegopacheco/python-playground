import asyncio

import httpx2

TIMEOUT = httpx2.Timeout(5.0, connect=2.0)
HEADERS = {"user-agent": "httpx2-poc"}


def build(base_url, **kwargs):
    return httpx2.Client(base_url=base_url, timeout=TIMEOUT, headers=HEADERS, **kwargs)


def health(client):
    return client.get("/health").raise_for_status().json()


def users(client):
    return client.get("/users").raise_for_status().json()["users"]


def echo(client, payload):
    return client.post("/echo", json=payload).raise_for_status().json()


def search(client, criteria):
    return client.query("/search", json=criteria).raise_for_status().json()["matches"]


def stream_lines(client, lines):
    with client.stream("GET", "/stream", params={"lines": lines}) as response:
        response.raise_for_status()
        return [line for line in response.iter_lines() if line]


def events(client, count):
    with client.sse("/events", params={"count": count}) as source:
        return [(event.event, event.json()) for event in source]


def secure(client, username, password):
    auth = httpx2.BasicAuth(username, password)
    return client.get("/secure", auth=auth).raise_for_status().json()


def status_error(client, code):
    try:
        client.get(f"/status/{code}").raise_for_status()
    except httpx2.HTTPStatusError as error:
        return error.response.status_code
    return None


def read_timeout(client, seconds):
    try:
        client.get("/delay", params={"seconds": seconds}, timeout=seconds / 2)
    except httpx2.ReadTimeout:
        return True
    return False


async def concurrent_health(base_url, times):
    async with httpx2.AsyncClient(base_url=base_url, timeout=TIMEOUT, headers=HEADERS) as client:
        responses = await asyncio.gather(*(client.get("/health") for _ in range(times)))
        return [response.raise_for_status().json()["status"] for response in responses]
