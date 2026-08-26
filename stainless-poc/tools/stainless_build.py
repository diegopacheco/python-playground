import io
import json
import os
import shutil
import sys
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = ROOT / "api" / "openapi.yml"
CONFIG_PATH = ROOT / "api" / "openapi.stainless.yml"
SDK_PATH = ROOT / "sdk"
BASE_URL = os.environ.get("STAINLESS_BASE_URL", "https://api.stainless.com")
TARGET = "python"
BRANCH = os.environ.get("STAINLESS_BRANCH", "main")
POLL_INTERVAL_SECONDS = 5
POLL_TIMEOUT_SECONDS = 900
FATAL_CONCLUSIONS = {"error", "fatal", "payment_required", "cancelled", "timed_out"}


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def env(name, default=None, required=False):
    value = os.environ.get(name, default)
    if required and not value:
        fail(f"{name} is not set")
    return value


def call(method, path, api_key, body=None, query=None):
    url = f"{BASE_URL}{path}"
    if query:
        url = f"{url}?{urllib.parse.urlencode(query)}"
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", f"Bearer {api_key}")
    request.add_header("Accept", "application/json")
    if data is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as error:
        payload = error.read().decode(errors="replace")
        try:
            return error.code, json.loads(payload)
        except json.JSONDecodeError:
            return error.code, {"message": payload}
    except urllib.error.URLError as error:
        fail(f"cannot reach {BASE_URL}: {error.reason}")


def expect(status, payload, ok, action):
    if status not in ok:
        fail(f"{action} failed with HTTP {status}: {json.dumps(payload)}")
    return payload


def revision():
    for path in (SPEC_PATH, CONFIG_PATH):
        if not path.is_file():
            fail(f"missing {path}")
    return {
        "openapi.yml": {"content": SPEC_PATH.read_text()},
        "openapi.stainless.yml": {"content": CONFIG_PATH.read_text()},
    }


def ensure_project(api_key, org, project):
    status, payload = call("GET", f"/v0/projects/{project}", api_key)
    if status == 200:
        print(f"project {org}/{project} found")
        return
    if status != 404:
        fail(f"cannot read project {project}: HTTP {status} {json.dumps(payload)}")
    print(f"project {project} not found, creating it under org {org}")
    body = {
        "org": org,
        "slug": project,
        "display_name": project,
        "targets": [TARGET],
        "revision": revision(),
    }
    status, payload = call("POST", "/v0/projects", api_key, body=body)
    expect(status, payload, {200, 201}, "project creation")
    print(f"project {org}/{project} created")


def create_build(api_key, project):
    body = {
        "project": project,
        "branch": BRANCH,
        "revision": revision(),
        "targets": [TARGET],
        "allow_empty": True,
        "commit_message": "feat(api): build taskly python sdk",
    }
    status, payload = call("POST", "/v0/builds", api_key, body=body)
    expect(status, payload, {200, 201}, "build creation")
    build_id = payload["id"]
    print(f"build {build_id} created on branch {BRANCH}")
    return build_id


def wait_for_build(api_key, build_id):
    deadline = time.monotonic() + POLL_TIMEOUT_SECONDS
    last_status = None
    while time.monotonic() < deadline:
        status, payload = call("GET", f"/v0/builds/{build_id}", api_key)
        expect(status, payload, {200}, "build lookup")
        target = payload.get("targets", {}).get(TARGET)
        if target is None:
            fail(f"build {build_id} has no {TARGET} target")
        commit = target.get("commit", {})
        current = (target.get("status"), commit.get("status"))
        if current != last_status:
            last_status = current
            print(f"build {build_id} {TARGET}: codegen={current[0]} commit={current[1]}")
        if commit.get("status") == "completed":
            return commit.get("conclusion")
        time.sleep(POLL_INTERVAL_SECONDS)
    fail(f"build {build_id} did not complete in {POLL_TIMEOUT_SECONDS}s")


def print_diagnostics(api_key, build_id):
    status, payload = call("GET", f"/v0/builds/{build_id}/diagnostics", api_key)
    if status != 200:
        return
    for item in payload.get("data", []):
        print(f"  [{item.get('level')}] {item.get('code')}: {item.get('message')}")


def download_source(api_key, build_id):
    query = {"build_id": build_id, "target": TARGET, "type": "source", "output": "url"}
    status, payload = call("GET", "/v0/build_target_outputs", api_key, query=query)
    expect(status, payload, {200}, "source output lookup")
    url = payload["url"]
    print(f"downloading {TARGET} sources")
    with urllib.request.urlopen(url) as response:
        archive = response.read()
    if SDK_PATH.exists():
        shutil.rmtree(SDK_PATH)
    SDK_PATH.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:*") as tar:
        members = tar.getmembers()
        roots = {member.name.split("/")[0] for member in members}
        strip = len(roots) == 1 and not any(m.name in roots and m.isfile() for m in members)
        for member in members:
            if strip:
                parts = member.name.split("/")[1:]
                if not parts:
                    continue
                member.name = "/".join(parts)
        tar.extractall(SDK_PATH, members=members, filter="data")
    if not (SDK_PATH / "pyproject.toml").is_file():
        fail(f"generated sources at {SDK_PATH} have no pyproject.toml")
    print(f"sdk written to {SDK_PATH}")


def main():
    api_key = env("STAINLESS_API_KEY", required=True)
    org = env("STAINLESS_ORG", required=True)
    project = env("STAINLESS_PROJECT", default="taskly")
    ensure_project(api_key, org, project)
    build_id = create_build(api_key, project)
    conclusion = wait_for_build(api_key, build_id)
    print(f"build {build_id} conclusion: {conclusion}")
    print_diagnostics(api_key, build_id)
    if conclusion in FATAL_CONCLUSIONS:
        fail(f"build {build_id} ended with conclusion {conclusion}")
    download_source(api_key, build_id)


if __name__ == "__main__":
    main()
