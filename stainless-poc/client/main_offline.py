import os

try:
    from taskly_offline import AuthenticatedClient
    from taskly_offline.api.status import get_status
    from taskly_offline.api.tasks import (
        create_task,
        delete_task,
        list_tasks,
        retrieve_task,
        update_task,
    )
    from taskly_offline.models import TaskCreate, TaskState, TaskUpdate
except ModuleNotFoundError:
    raise SystemExit("the taskly offline sdk is not installed, run ./generate-sdk-offline.sh first")


def main():
    client = AuthenticatedClient(
        base_url=os.environ.get("TASKLY_BASE_URL", "http://localhost:8080"),
        token=os.environ.get("TASKLY_API_KEY", "local-token"),
    )

    print("status:", get_status.sync(client=client).message)

    task = create_task.sync(
        client=client,
        body=TaskCreate(
            title="wire the generated sdk",
            details="call every endpoint of the taskly api",
            state=TaskState.PENDING,
        ),
    )
    print("created:", task.id, task.title, task.state)

    task = update_task.sync(task.id, client=client, body=TaskUpdate(state=TaskState.DOING))
    print("updated:", task.id, task.state)

    fetched = retrieve_task.sync(task.id, client=client)
    print("retrieved:", fetched.id, fetched.title, fetched.details)

    listed = list_tasks.sync(client=client, state=TaskState.DOING)
    print("listed:", [item.title for item in listed.data])

    deleted = delete_task.sync(task.id, client=client)
    print("deleted:", deleted.id)

    print("remaining:", len(list_tasks.sync(client=client).data))


if __name__ == "__main__":
    main()
