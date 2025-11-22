from typing import AsyncIterator, TypeVar

import pytest

from simple_sqs.queue_client import QueueClient


@pytest.fixture
async def queue(sqs_client):
    queue_name = "test_queue"
    await sqs_client.create_queue(QueueName=queue_name)
    return queue_name


@pytest.fixture
async def client(sqs_client, queue):
    return QueueClient(sqs_client, queue)


T = TypeVar("T")


async def head(ait: AsyncIterator[T], n: int) -> AsyncIterator[T]:
    if n == 0:
        return

    async for item in ait:
        yield item
        n -= 1
        if n == 0:
            return


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "messages",
    [
        ["abcd"],
        ["a", "b", "c", "d"],
        ["a"] * 10,
    ],
)
@pytest.mark.parametrize(
    "delay",
    [
        0,
        1,
    ],
)
async def test_multiple_messages(client: QueueClient, messages: list[str], delay: int):
    for message in messages:
        await client.produce(message, delay=delay)

    actual = []
    async for message in head(client.consume(), len(messages)):
        actual.append(message.get("Body"))
        await client.ack(message)
    assert actual == messages


async def test_delay(client):
    await client.produce("a", delay=1)
    await client.produce("b")
    actual = []
    async for message in head(client.consume(), 2):
        actual.append(message.get("Body"))
        await client.ack(message)

    assert actual == ["b", "a"]


async def test_nack(client):
    await client.produce("a")
    await client.produce("b")
    async for message in head(client.consume(), 1):
        await client.nack(message, 1)

    actual = []
    async for message in head(client.consume(), 2):
        actual.append(message.get("Body"))
        await client.ack(message)

    assert actual == ["b", "a"]
