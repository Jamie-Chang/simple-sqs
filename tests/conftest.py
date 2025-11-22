from typing import AsyncIterator

import aiobotocore.session
import pytest
from aiobotocore.config import AioConfig
from moto.server import ThreadedMotoServer


@pytest.fixture
def server_scheme():
    return "http"


@pytest.fixture
def signature_version():
    return "v4"


@pytest.fixture
async def moto_server(server_scheme) -> AsyncIterator[str]:
    server = ThreadedMotoServer(port=0)
    try:
        server.start()
        host, port = server.get_host_and_port()
        yield f"http://{host}:{port}"
    finally:
        server.stop()


@pytest.fixture
def session() -> aiobotocore.session.AioSession:
    session = aiobotocore.session.AioSession()
    return session


@pytest.fixture
def region() -> str:
    return "us-east-1"


@pytest.fixture
def config(region, signature_version):
    return AioConfig(
        region_name=region,
        signature_version=signature_version,
        read_timeout=5,
        connect_timeout=5,
    )


@pytest.fixture
def aws_auth():
    return {"aws_secret_access_key": "xxx", "aws_access_key_id": "xxx"}


@pytest.fixture
async def sqs_client(session, region, config, moto_server, aws_auth):
    kw = {"endpoint_url": moto_server, **aws_auth}
    async with session.create_client(
        "sqs", region_name=region, config=config, **kw
    ) as client:
        yield client
