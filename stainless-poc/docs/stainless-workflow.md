# Stainless workflow

## The two inputs

Stainless reads two files, and both are sent on every build.

| File | Sent as | Role |
| --- | --- | --- |
| `api/openapi.yml` | `openapi.yml` | What the API is: paths, schemas, auth, errors |
| `api/openapi.stainless.yml` | `openapi.stainless.yml` | What the SDK is: resource tree, method names, package, client options |

The revision key names are the ones Stainless expects in a project config repo. Changing them makes the build
ignore the file.

## What `tools/stainless_build.py` calls

All calls go to `https://api.stainless.com` with `Authorization: Bearer $STAINLESS_API_KEY`.

| Step | Call | Notes |
| --- | --- | --- |
| 1 | `GET /v0/projects/{project}` | A 404 means the project has to be created first |
| 2 | `POST /v0/projects` | Sends `org`, `slug`, `display_name`, `targets: [python]` and the revision |
| 3 | `POST /v0/builds` | Sends the revision, `branch`, `targets: [python]`, `allow_empty: true` |
| 4 | `GET /v0/builds/{id}` | Polled every 5s for up to 15 minutes |
| 5 | `GET /v0/builds/{id}/diagnostics` | Printed after the build, whatever the outcome |
| 6 | `GET /v0/build_target_outputs` | `type=source&output=url` returns a tarball link |

A build target reports two statuses. `targets.python.status` is the codegen phase
(`not_started`, `codegen`, `postgen`, `completed`) and `targets.python.commit.status` is the commit
(`queued`, `in_progress`, `completed`). The script waits for the commit status, because the conclusion is only
final there.

Conclusions treated as failures: `error`, `fatal`, `payment_required`, `cancelled`, `timed_out`. `warning`,
`note`, `success`, `noop` and `version_bump` let the download proceed.

The tarball has a single top level directory, which the script strips so `sdk/pyproject.toml` ends up at the
root of `sdk/`. The script refuses to continue if that file is missing.

## Config to SDK mapping

```yaml
resources:
  $client:
    methods:
      status: get /status
  tasks:
    models:
      task: "#/components/schemas/Task"
    methods:
      create: post /tasks
      retrieve: get /tasks/{task_id}
      update: put /tasks/{task_id}
      list: get /tasks
      delete: delete /tasks/{task_id}
```

- `$client` puts a method on the client itself: `client.status()`.
- Every other key is a namespace: `client.tasks.create(...)`.
- `models` names the type that is exported for the resource: `taskly.types.Task`.
- Method names are yours; the endpoint on the right is what gets called.

```yaml
client_settings:
  opts:
    api_key:
      type: string
      nullable: true
      auth:
        security_scheme: BearerAuth
      read_env: TASKLY_API_KEY
```

`BearerAuth` is the security scheme declared in the OpenAPI document. Binding it here turns it into the
`api_key` constructor argument, which falls back to the `TASKLY_API_KEY` environment variable.

```yaml
environments:
  local: http://localhost:8080

targets:
  python:
    edition: python.2025-11-20
    package_name: taskly
    project_name: taskly
```

`package_name` is the import name, `project_name` is the distribution name. `environments` becomes the
`environment="local"` client argument; the client also accepts `base_url` directly, which is what
`client/main.py` uses.

An edition pins the generator behaviour. `python.2025-11-20` uses uv as the package manager for the generated
repository.

## Iterating

Change `api/openapi.yml` or `api/openapi.stainless.yml` and run `./generate-sdk.sh` again. Every run creates a
new build on the same branch, replaces `sdk/`, and reinstalls the package into `.venv`. Set `STAINLESS_BRANCH`
to build on a different Stainless branch without touching `main`.
