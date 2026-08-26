# Troubleshooting

## `STAINLESS_API_KEY is not set`

Create a key in your organization settings at [app.stainless.com](https://app.stainless.com), then export it.
`STAINLESS_ORG` must be the organization name, not the display name.

## `project creation failed with HTTP 403`

The API key belongs to a different organization than `STAINLESS_ORG`, or the account cannot create projects.

## `build ... conclusion: error` or `fatal`

The generator still produced output, but it is not usable. The diagnostics printed right after the conclusion
name the endpoint or schema at fault. Common causes in an OpenAPI document:

- a `$ref` that does not resolve
- a method in `openapi.stainless.yml` pointing at an endpoint the spec does not declare
- a security scheme referenced by `client_settings.opts` that is missing from `components.securitySchemes`

Fix the input files and run `./generate-sdk.sh` again.

## `conclusion: payment_required`

The organization has no active plan for this target.

## `build ... did not complete in 900s`

Builds are queued server side. Re-run the script; it creates a new build rather than resuming the old one.

## `the taskly sdk is not installed`

`./generate-sdk.sh` never finished, or the venv was rebuilt afterwards. Run it again; it installs `sdk/` into
`.venv` at the end.

## `cannot reach https://api.stainless.com`

Network or proxy problem. `STAINLESS_BASE_URL` overrides the endpoint if you need to point somewhere else.

## Client fails with a connection error

The server is not running. `./run-server.sh` in another shell, or use `./run-all.sh` which handles both sides.

## Client fails with 401

The server accepts any non empty bearer token. A 401 means none was sent, which points at `api_key` being
`None`: pass it to the constructor or export `TASKLY_API_KEY`.

## Port 8080 is taken

Export `TASKLY_PORT` for the server and `TASKLY_BASE_URL` for the client.
