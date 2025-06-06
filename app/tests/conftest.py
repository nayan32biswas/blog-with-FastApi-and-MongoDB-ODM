import logging
from typing import Any

import pytest
from fastapi.testclient import TestClient
from mongodb_odm import connect, disconnect

from app.base import config
from app.main import app
from cli.management_command.data_population import clean_data, populate_dummy_data

logger = logging.getLogger(__name__)
client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def onetime_setup() -> Any:
    """
    This fixture runs once per test session to set up the database connection
    and populate it with dummy data.
    """

    connect(config.TEST_MONGO_URL)

    clean_data()
    populate_dummy_data(total_user=10, total_post=10, is_unittest=True)

    yield None

    disconnect()
