# Pre-built Houses Webhooks

A construction site that sells pre-built houses emits a signed webhook every time a house is ordered or
moves one construction stage. The webhooks go out to a public relay on the internet (smee.io), a
listener subscribes to that relay, verifies every signature and stores the events, and a light themed
admin UI shows everything the listener got. Pure Python standard library, no third party packages.

## How it Works

1. `scripts/setup.sh` asks smee.io for a fresh random channel and generates a random webhook secret.
   Both go to `.run/relay.env` (git ignored, mode 600), never into the repository.
2. `scripts/start-all.sh` starts the listener first and waits until it is subscribed to the channel
   (Server-Sent Events), then the webhook server and the admin UI.
3. `generate-synthetical-data.sh` orders random synthetic houses and advances each through some stages.
4. For every change the webhook server POSTs a JSON event to the public smee.io URL with
   `X-Webhook-Event`, `X-Webhook-Timestamp` and `X-Webhook-Signature` (HMAC SHA-256).
5. smee.io pushes the event to the listener over its SSE stream.
6. The listener keeps only the body and the three webhook headers, recomputes the signature,
   de-duplicates by event id and writes the event to SQLite.
7. The admin UI proxies `/api/events` to the listener and refreshes every 2 seconds.

## Architecture

![Architecture](printscreens/architecture.svg)

## Features

| Feature | Why |
|---|---|
| Public relay (smee.io) | The webhook really crosses the internet through a public IP, no tunnel, no router config. |
| HMAC SHA-256 signature | The smee.io channel is public, so anyone could POST to it. Only events signed with the secret show as valid. |
| Timestamp in the signature | A captured signature cannot be replayed with another timestamp. |
| Header allow list | smee.io forwards `client-ip` and `x-forwarded-for`; the listener drops them so no IP is stored or shown. |
| De-duplication | An SSE reconnect cannot store the same event twice. |
| Loud delivery failures | If the relay is down the server answers `502` instead of a silent success. |
| Construction lifecycle | `ORDERED -> BUILDING_IN_FACTORY -> SHIPPED -> ARRIVED_ON_SITE -> ASSEMBLED -> INSPECTED -> DELIVERED`, no skipping or going past delivered. |
| Admin UI | Counters, filter by event type, click a row to see the raw payload. Rendered with `textContent`, so a hostile payload cannot inject HTML. |
| Synthetic data only | Models, lots (`Lot C-12`) and buyer aliases (`buyer-0042`) are generated, nothing personal. |

## Stack

| Tech | Why |
|---|---|
| Python 3.10+ standard library | `http.server`, `urllib`, `hmac`, `sqlite3`, `threading`: zero dependencies to install. |
| smee.io | Free public webhook relay with an SSE stream, built exactly for receiving webhooks locally. |
| SQLite | Listener events survive restarts in a single file under `.run/data`. |
| Vanilla JS, HTML, CSS | The admin UI needs no framework or build step. |
| unittest | Tests run with the interpreter, nothing to install. |
| bash + curl | Operational scripts and the synthetic data generator. |

## APIs

Webhook server, http://localhost:8081

| Method | Path | Body | Response |
|---|---|---|---|
| GET | `/api/models` | | catalog of house models |
| GET | `/api/houses` | | all houses |
| POST | `/api/houses` | `{"model": "aspen", "lot": "Lot A-01", "buyer_alias": "buyer-0001"}` | `201` house, sends `house.ordered`; `400` invalid; `502` relay down |
| POST | `/api/houses/{id}/advance` | | `200` sends `house.status_changed` or `house.delivered`; `404`; `409` already delivered |

Listener, http://localhost:8082

| Method | Path | Response |
|---|---|---|
| GET | `/api/events` | stored events, newest first |
| GET | `/health` | `{"status": "UP", "relay_connected": true}` |

Admin UI, http://localhost:8083 serves the page and proxies `/api/events` and `/health` to the listener.

Webhook sent to the relay:

```
POST https://smee.io/<random channel>
X-Webhook-Event: house.delivered
X-Webhook-Timestamp: 1789000000
X-Webhook-Signature: sha256=hex(hmac_sha256(secret, "<timestamp>.<canonical json body>"))
```

```json
{
  "id": "06d61902-edb7-479a-b2a6-3ec3c1d48a23",
  "type": "house.delivered",
  "created_at": "2026-09-16T16:20:46+00:00",
  "data": {
    "previous_status": "INSPECTED",
    "house": {
      "id": "3fb68249-bf0f-4297-8042-6022f1d9ca27",
      "model": "cedar",
      "model_details": {"name": "Cedar 4BR Two Story", "bedrooms": 4, "sqft": 2100, "price_usd": 348000},
      "lot": "Lot F-09",
      "buyer_alias": "buyer-1586",
      "status": "DELIVERED",
      "updated_at": "2026-09-16T16:20:46+00:00"
    }
  }
}
```

## Design Decisions

* The signature is computed over canonical JSON (sorted keys, no spaces). smee.io parses and
  re-serializes the body, so signing the raw bytes would break; the listener re-canonicalizes and compares
  with `hmac.compare_digest`. Payloads use integers only so number formatting cannot differ.
* The listener stores events with signature `rejected` instead of dropping them, so forged traffic on the
  public channel is visible in the admin UI.
* The listener starts first and `start-all.sh` waits for the relay `ready` event, because smee.io does
  not buffer: a webhook sent before anyone subscribes is lost.
* The house store is in memory on purpose; the durable record of what happened is the listener database.
* The channel URL and secret are never printed, logged or shown in the UI. Anyone with the channel URL
  can read the stream, which is fine only because every payload is synthetic.
* Layout: `app/houses.py` domain, `app/publisher.py` sends, `app/subscriber.py` receives,
  `app/event_store.py` SQL, `app/signing.py` shared by both sides, one small HTTP entry point per component.

## Privacy

smee.io, like any public service, sees the source IP of the machine that sends the webhook and of the
listener that subscribes. The project does not store or display it, and no local path, user name or
real data is sent: only generated houses.

## Printscreens

All events received by the listener. The green dot says the listener is subscribed to the public relay,
the counters show 33 events, all with valid signatures, and each row is one webhook with its house,
model, lot and the stage it reached.

![All events](printscreens/admin-all-events.png)

Filter chips by event type. Here only `house.delivered` is selected, the final webhook of the two houses
that went through every construction stage.

![Delivered filter](printscreens/admin-filter-delivered.png)

Clicking a row opens the raw signed payload exactly as it arrived through smee.io, with the previous
status and the model details.

![Event payload](printscreens/admin-event-payload.png)

## Scripts

All scripts live in `scripts/` and run from any directory of the repository.

| Script | What it does |
|---|---|
| `./scripts/setup.sh` | Checks python3, curl and lsof, creates the smee.io channel and webhook secret |
| `./scripts/start-all.sh` | Starts listener, webhook server and admin UI and prints the full link of each one |
| `./scripts/status.sh` | Shows every service port as UP or DOWN and whether the relay is connected |
| `./scripts/test-all.sh` | Runs every test suite |
| `./scripts/ui.sh` | Opens the admin UI in the browser |
| `./scripts/stop-all.sh` | Stops every service |
| `./generate-synthetical-data.sh [houses]` | Orders synthetic houses (default 5) and advances them, which sends the webhooks |

Ports are declared in `scripts/ports.env`: webhook_server 8081, listener 8082, admin_ui 8083.

```bash
./scripts/setup.sh
./scripts/start-all.sh
./generate-synthetical-data.sh 6
./scripts/ui.sh
./scripts/test-all.sh
./scripts/stop-all.sh
```
