import os

try:
    from taskly import Taskly
except ModuleNotFoundError:
    raise SystemExit("the taskly sdk is not installed, run ./generate-sdk.sh first")


def main():
    client = Taskly(
        api_key=os.environ.get("TASKLY_API_KEY", "local-token"),
        base_url=os.environ.get("TASKLY_BASE_URL", "http://localhost:8080"),
    )

    print("status:", client.status().message)

    task = client.tasks.create(
        title="wire the generated sdk",
        details="call every endpoint of the taskly api",
        state="pending",
    )
    print("created:", task.id, task.title, task.state)

    task = client.tasks.update(task.id, state="doing")
    print("updated:", task.id, task.state)

    fetched = client.tasks.retrieve(task.id)
    print("retrieved:", fetched.id, fetched.title, fetched.details)

    listed = client.tasks.list(state="doing")
    print("listed:", [item.title for item in listed.data])

    deleted = client.tasks.delete(task.id)
    print("deleted:", deleted.id)

    print("remaining:", len(client.tasks.list().data))


if __name__ == "__main__":
    main()
