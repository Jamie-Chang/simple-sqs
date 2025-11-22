# simple-async-sqs
`simple-async-sqs` is a opinionated minimalistic async Python client to interact with SQS. 

`simple-async-sqs` is for developers who are tired of repeated configurations in task frameworks and prefer a simple message processing library. 


## Installation

```bash
uv add simple-async-sqs
```

Optionally add the type stubs for used in development:

```bash
uv add --dev simple-async-sqs[stubs]
```

## Usage
A consumer can be simply created by `Client.consume` which is simply an `AsyncIterator`.

Messages must be either ack'd or nack'd after processing.
```py
import asyncio

from simple_async_sqs.queue_client import QueueClient


async def process(client: QueueClient):
    async for message in client.consume():
        try:
            print(message.get("Body"))
            ...
        except Exception:
            await client.nack(message, retry_timeout=20)
        else:
            await client.ack(message)


async def process_single():
    async with QueueClient.create("my-queue") as client:
        await process(client)
```

We can also easily parallelise the work here using `asyncio.TaskGroup`:

```py
async def process_parallel(workers: int):
    async with QueueClient.create("my-queue") as client:
        async with asyncio.TaskGroup() as tg:
            for _ in range(workers):
                tg.create_task(process(client))
```

### Producer
We can simply produce a message by:
```py
await client.producer("my_message_payload", delay=10)
```
