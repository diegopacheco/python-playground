import hashlib
import json
import os
import re

import requests
import vcr
import yaml

API_HOST = "http://api.vcr.local"
CASSETTE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cassettes"))

RECORDER = vcr.VCR(
    cassette_library_dir=CASSETTE_DIR,
    serializer="yaml",
    match_on=["method", "path"],
)


class NoTape(Exception):
    pass


def slug(path, query=""):
    base = path.strip("/").replace("/", "_")
    if query:
        base += "__" + hashlib.sha1(query.encode("utf-8")).hexdigest()[:8]
    return re.sub(r"[^A-Za-z0-9_.-]", "-", base)


def file_of(name):
    return os.path.join(CASSETTE_DIR, name + ".yaml")


def uri_of(path, query=""):
    return API_HOST + path + (("?" + query) if query else "")


def exists(path, query=""):
    return os.path.exists(file_of(slug(path, query)))


def write(method, path, payload, query="", status=200):
    name = slug(path, query)
    document = {
        "version": 1,
        "interactions": [
            {
                "request": {
                    "method": method,
                    "uri": uri_of(path, query),
                    "body": None,
                    "headers": {"Accept": ["application/json"]},
                },
                "response": {
                    "status": {"code": status, "message": "OK"},
                    "headers": {"Content-Type": ["application/json"], "X-Taped-Endpoint": [path]},
                    "body": {"string": json.dumps(payload)},
                },
            }
        ],
    }
    os.makedirs(CASSETTE_DIR, exist_ok=True)
    with open(file_of(name), "w") as handle:
        yaml.safe_dump(document, handle, sort_keys=False, allow_unicode=True, width=100)
    return name + ".yaml"


def read(path, query=""):
    name = slug(path, query)
    if not os.path.exists(file_of(name)):
        raise NoTape(path)
    with open(file_of(name)) as handle:
        document = yaml.safe_load(handle)
    return json.loads(document["interactions"][0]["response"]["body"]["string"])


def play(method, path, query=""):
    name = slug(path, query)
    if not os.path.exists(file_of(name)):
        raise NoTape(path)
    with RECORDER.use_cassette(name + ".yaml", record_mode="none") as cassette:
        response = requests.request(method, uri_of(path, query), timeout=5)
        return response, {"cassette": name + ".yaml", "played": cassette.play_count}


def eject(prefix):
    if not os.path.isdir(CASSETTE_DIR):
        return []
    dropped = [f for f in sorted(os.listdir(CASSETTE_DIR)) if f.startswith(prefix) and f.endswith(".yaml")]
    for name in dropped:
        os.remove(os.path.join(CASSETTE_DIR, name))
    return dropped


def catalog():
    if not os.path.isdir(CASSETTE_DIR):
        return []
    items = []
    for name in sorted(os.listdir(CASSETTE_DIR)):
        if not name.endswith(".yaml"):
            continue
        full = os.path.join(CASSETTE_DIR, name)
        with open(full) as handle:
            document = yaml.safe_load(handle)
        interaction = document["interactions"][0]
        items.append(
            {
                "name": name,
                "bytes": os.path.getsize(full),
                "method": interaction["request"]["method"],
                "uri": interaction["request"]["uri"],
                "status": interaction["response"]["status"]["code"],
            }
        )
    return items
