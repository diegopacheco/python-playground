import json
import os
import sys
import urllib.error
import urllib.request

from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("POSTHOG_API_HOST", "https://us.posthog.com").rstrip("/")
PROJECT_ID = os.getenv("POSTHOG_PROJECT_ID", "598105")
DASHBOARD_ID = os.getenv("POSTHOG_DASHBOARD_ID", "2078376")
DASHBOARD_NAME = os.getenv("POSTHOG_DASHBOARD_NAME", "DVD metrics")
WINDOW_DAYS = int(os.getenv("POSTHOG_WINDOW_DAYS", "30"))
KEY_VARIABLE = "POSTHOG_PERSONAL_API_KEY"


def trends(event: str, label: str, math: str = "total", math_property: str | None = None):
    series: dict[str, object] = {"kind": "EventsNode", "event": event, "name": label, "math": math}
    if math_property is not None:
        series["math_property"] = math_property
    return {
        "kind": "InsightVizNode",
        "source": {
            "kind": "TrendsQuery",
            "series": [series],
            "interval": "day",
            "dateRange": {"date_from": f"-{WINDOW_DAYS}d"},
            "trendsFilter": {"display": "ActionsLineGraph"},
        },
    }


def table(sql: str):
    return {
        "kind": "DataTableNode",
        "source": {"kind": "HogQLQuery", "query": sql},
    }


TOP_RENTED_SQL = f"""
SELECT properties.title AS dvd,
       count() AS rentals
FROM events
WHERE event = 'dvd_rented'
  AND timestamp >= now() - INTERVAL {WINDOW_DAYS} DAY
GROUP BY dvd
ORDER BY rentals DESC
LIMIT 5
""".strip()

NEVER_RENTED_SQL = f"""
SELECT properties.title AS dvd,
       count() AS times_reported_never_rented
FROM events
WHERE event = 'dvd_never_rented'
  AND timestamp >= now() - INTERVAL {WINDOW_DAYS} DAY
GROUP BY dvd
ORDER BY times_reported_never_rented DESC
LIMIT 5
""".strip()

INSIGHTS = [
    {
        "name": "DVD rentals over time",
        "description": "Counter of dvd_rented, the base signal for every rental ranking.",
        "query": trends("dvd_rented", "rentals"),
    },
    {
        "name": "Missed rental deadlines over time",
        "description": "Counter of dvd_deadline_missed, emitted once per late rental.",
        "query": trends("dvd_deadline_missed", "missed deadlines"),
    },
    {
        "name": "Idle DVDs per rollup window",
        "description": "Average idle_count from dvds_idle_rollup: titles that earned nothing in the window.",
        "query": trends("dvds_idle_rollup", "idle dvds", math="avg", math_property="idle_count"),
    },
    {
        "name": "Top 5 most rented DVDs",
        "description": "Busiest titles by dvd_rented count.",
        "query": table(TOP_RENTED_SQL),
    },
    {
        "name": "Top 5 never rented DVDs",
        "description": "Titles most often reported as never rented by the rollup worker.",
        "query": table(NEVER_RENTED_SQL),
    },
]


def api_key() -> str:
    key = os.getenv(KEY_VARIABLE)
    if not key:
        sys.exit(
            f"{KEY_VARIABLE} is not set.\n"
            "Create one under Settings -> Personal API keys with scopes "
            "insight:write and dashboard:write, then add it to the local env file."
        )
    return key


def call(method: str, path: str, body: dict | None = None) -> dict:
    request = urllib.request.Request(
        f"{HOST}{path}",
        method=method,
        data=None if body is None else json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {api_key()}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read() or "{}")
    except urllib.error.HTTPError as error:
        detail = error.read().decode()[:600]
        raise SystemExit(f"{method} {path} failed with {error.code}: {detail}") from None


def validate(spec: dict) -> None:
    call("POST", f"/api/projects/{PROJECT_ID}/query/", {"query": spec["query"]["source"]})


def existing_by_name() -> dict[str, int]:
    found: dict[str, int] = {}
    page = f"/api/projects/{PROJECT_ID}/insights/?limit=100"
    while page:
        payload = call("GET", page)
        for insight in payload.get("results", []):
            if insight.get("name"):
                found.setdefault(insight["name"], insight["id"])
        following = payload.get("next")
        page = following.replace(HOST, "") if following else None
    return found


def main() -> None:
    apply = "--apply" in sys.argv

    project = call("GET", f"/api/projects/{PROJECT_ID}/")
    dashboard = call("GET", f"/api/projects/{PROJECT_ID}/dashboards/{DASHBOARD_ID}/")
    print(f"project  : {project.get('name')} ({PROJECT_ID})")
    print(f"dashboard: {dashboard.get('name')} ({DASHBOARD_ID})")

    print("\nvalidating queries against the live API")
    for spec in INSIGHTS:
        validate(spec)
        print(f"  ok  {spec['name']}")

    if not apply:
        print("\ndry run only, nothing was created. re-run with --apply")
        return

    if dashboard.get("name") != DASHBOARD_NAME:
        renamed = call(
            "PATCH",
            f"/api/projects/{PROJECT_ID}/dashboards/{DASHBOARD_ID}/",
            {"name": DASHBOARD_NAME},
        )
        print(f"\nrenamed dashboard to {renamed.get('name')!r}")

    known = existing_by_name()
    print("\nwriting insights")
    for spec in INSIGHTS:
        body = {
            "name": spec["name"],
            "description": spec["description"],
            "query": spec["query"],
            "dashboards": [int(DASHBOARD_ID)],
        }
        if spec["name"] in known:
            insight = call(
                "PATCH", f"/api/projects/{PROJECT_ID}/insights/{known[spec['name']]}/", body
            )
            print(f"  updated {insight['id']}  {spec['name']}")
        else:
            insight = call("POST", f"/api/projects/{PROJECT_ID}/insights/", body)
            print(f"  created {insight['id']}  {spec['name']}")

    final = call("GET", f"/api/projects/{PROJECT_ID}/dashboards/{DASHBOARD_ID}/")
    tiles = final.get("tiles", [])
    print(f"\ndashboard now has {len(tiles)} tiles:")
    for tile in tiles:
        insight = tile.get("insight") or {}
        print(f"  - {insight.get('name')}")
    print(f"\n{HOST}/project/{PROJECT_ID}/dashboard/{DASHBOARD_ID}")


if __name__ == "__main__":
    main()
