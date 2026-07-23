import asyncio
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker

TASK_QUEUE = "python-essentials-queue"


@activity.defn
async def greet(name: str) -> str:
    return f"hello {name}"


@activity.defn
async def shout(text: str) -> str:
    return text.upper()


@workflow.defn
class GreetingWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        greeting = await workflow.execute_activity(
            greet, name, start_to_close_timeout=timedelta(seconds=10)
        )
        return await workflow.execute_activity(
            shout, greeting, start_to_close_timeout=timedelta(seconds=10)
        )


async def main():
    client = await Client.connect("localhost:7233")

    async with Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[GreetingWorkflow],
        activities=[greet, shout],
    ):
        result = await client.execute_workflow(
            GreetingWorkflow.run,
            "alice",
            id="python-essentials-workflow",
            task_queue=TASK_QUEUE,
        )
        print("workflow result:", result)


if __name__ == "__main__":
    asyncio.run(main())
