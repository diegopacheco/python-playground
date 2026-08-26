# Offline lane

Stainless runs its generator on its own servers, so `./generate-sdk.sh` needs an organization and an API key.
The offline lane exists so the round trip is runnable without one. It reads the same `api/openapi.yml` and
generates a client locally with [openapi-python-client](https://github.com/openapi-generators/openapi-python-client).

```bash
./generate-sdk-offline.sh
./run-all.sh
```

`api/openapi-python-client.yml` only renames the output, so the package does not collide with the Stainless
one:

```yaml
project_name_override: taskly-offline
package_name_override: taskly_offline
```

## What changes

| | Stainless lane | Offline lane |
| --- | --- | --- |
| Command | `./generate-sdk.sh` | `./generate-sdk-offline.sh` |
| Needs an account | yes | no |
| Runs | on api.stainless.com | on your machine |
| Output | `sdk/`, package `taskly` | `sdk-offline/`, package `taskly_offline` |
| Client | `client/main.py` | `client/main_offline.py` |
| Shaped by | `api/openapi.stainless.yml` | the OpenAPI document alone |

## What the call sites look like

Stainless builds a resource tree from the config, so the spec's `operationId` never shows up:

```python
from taskly import Taskly

client = Taskly(api_key="local-token", base_url="http://localhost:8080")
task = client.tasks.create(title="wire the generated sdk", state="pending")
client.tasks.update(task.id, state="doing")
client.status()
```

The offline generator has no config to read, so it derives one module per operation, grouped by tag, and the
client is passed in on every call:

```python
from taskly_offline import AuthenticatedClient
from taskly_offline.api.tasks import create_task, update_task
from taskly_offline.api.status import get_status
from taskly_offline.models import TaskCreate, TaskState, TaskUpdate

client = AuthenticatedClient(base_url="http://localhost:8080", token="local-token")
task = create_task.sync(client=client, body=TaskCreate(title="wire the generated sdk", state=TaskState.PENDING))
update_task.sync(task.id, client=client, body=TaskUpdate(state=TaskState.DOING))
get_status.sync(client=client)
```

Other differences worth knowing:

- `state` is a `str` `Enum` here; Stainless renders it as `Literal[...]` so unknown values from a newer server
  still parse.
- Request bodies are explicit model objects rather than keyword arguments.
- Errors come back as an `Error` model in the return union instead of being raised, unless the client is built
  with `raise_on_unexpected_status=True`.
- There is no retry, pagination or streaming layer; Stainless generates those from the config.

That gap is the point of the POC: the same document produces a usable client either way, and the Stainless
config is what buys the shape.

## Which client runs

`run-client.sh` and `run-all.sh` prefer `taskly` when it is installed and fall back to `taskly_offline`, and
print which one they picked. Installing both is fine; they are separate packages.
