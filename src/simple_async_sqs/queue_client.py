from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, AsyncIterator

import aiobotocore
import aiobotocore.session

if TYPE_CHECKING:
    from types_aiobotocore_sqs.client import SQSClient
    from types_aiobotocore_sqs.type_defs import MessageTypeDef


@dataclass
class QueueClient:
    client: SQSClient
    queue: str
    wait_time: int = 20

    @asynccontextmanager
    @classmethod
    async def create(
        cls,
        queue: str,
        wait_time: int = 20,
        **sqs_options: object,
    ) -> AsyncIterator[QueueClient]:
        session = aiobotocore.session.get_session(**sqs_options)
        async with session.create_client("sqs") as client:
            yield QueueClient(client, queue, wait_time)

    async def produce(self, message: str, delay: int = 0) -> None:
        await self.client.send_message(
            QueueUrl=self.queue,
            MessageBody=message,
            DelaySeconds=delay,
        )

    async def consume(self, timeout: int = 30) -> AsyncIterator[MessageTypeDef]:
        while True:
            messages = await self.client.receive_message(
                QueueUrl=self.queue,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=self.wait_time,
                VisibilityTimeout=timeout,
            )
            match messages:
                case {"Messages": [message]}:
                    yield message
                case _:
                    continue

    async def heartbeat(self, message: MessageTypeDef, timeout: int = 30) -> None:
        assert "ReceiptHandle" in message
        await self.client.change_message_visibility(
            QueueUrl=self.queue,
            ReceiptHandle=message["ReceiptHandle"],
            VisibilityTimeout=timeout,
        )

    async def ack(self, message: MessageTypeDef) -> None:
        assert "ReceiptHandle" in message
        await self.client.delete_message(
            QueueUrl=self.queue,
            ReceiptHandle=message["ReceiptHandle"],
        )

    async def nack(self, message: MessageTypeDef, retry_timeout: int) -> None:
        assert "ReceiptHandle" in message
        await self.client.change_message_visibility(
            QueueUrl=self.queue,
            ReceiptHandle=message["ReceiptHandle"],
            VisibilityTimeout=retry_timeout,
        )
