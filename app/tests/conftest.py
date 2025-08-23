import logging
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mongodb_odm import adisconnect, connect

from app.base import config
from app.main import app

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture(autouse=True)
async def db_connection() -> AsyncGenerator[None, None]:
    """
    This fixture establishes a database connection for each test function.
    """
    # Connect to test database with async enabled for this test
    connect(config.TEST_MONGO_URL, async_is_enabled=True)

    yield

    # Disconnect after test
    await adisconnect()


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async client for testing"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
