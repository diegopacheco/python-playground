# Changelog

Records every user-visible change to the python3-httpx2 proof of concept.

## 1.0.0 - 2026-08-28

### Added

- `build.sh` creates a Python 3.14.6 virtual environment, installs the pinned dependencies, and byte-compiles the sources.
- `run.sh` starts the local HTTP server in the foreground on port 8080, overridable with the `PORT` variable.
- `test-client.sh` walks every client scenario and prints the result of each, starting a server first when the port is free and shutting it down afterwards.
- `test.sh` runs the test suite against a server bound to a free port chosen at run time, so it never collides with a server left running.
- A local HTTP server built only from the standard library, serving health, user listing, body echo, filtered search, chunked streaming, server-sent events, basic-auth, arbitrary status codes, and a delayed reply.
- Client coverage of the two calls that HTTPX never had: `QUERY` requests that carry a JSON body, and server-sent events read as decoded event objects rather than raw lines.
- Client coverage of streaming reads, concurrent async requests, basic authentication, status-code errors, and per-request read timeouts.
- A test that drives the same client functions through a mock transport, so the client can be checked with no server and no open port.
- `index.html`, a self-contained page describing the endpoints and the client calls, with line-numbered and highlighted code.
- `architecture.png` and its `architecture.svg` source, showing how a request travels from the entry points down to the server.

### Verified

- The full suite runs green: 12 passed, 0 skipped, in 1.05s on Python 3.14.6 with httpx2 2.12.0.
- `test-client.sh` completes every scenario: health returns ok, the four seeded users come back, `QUERY /search` filters to ada and guido, streaming yields 4 lines, 3 server-sent events decode, basic auth returns the admin user, a 503 surfaces as an error, a read timeout fires, and 5 concurrent async requests all return ok.
- `build.sh` reports Python 3.14.6 and httpx2 2.12.0 and compiles both source and test packages without warnings.
