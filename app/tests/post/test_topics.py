from faker import Faker
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.tests.endpoints import Endpoints
from app.tests.post.helper import create_topic
from app.tests.utils import get_header

client = TestClient(app)
fake = Faker()


def test_get_topics() -> None:
    response = client.get(Endpoints.TOPICS)
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.json()


def test_get_topics_search() -> None:
    search_text = "something"

    create_topic(search_text)

    response = client.get(Endpoints.TOPICS, params={"q": search_text})
    assert response.status_code == status.HTTP_200_OK


def test_create_topics() -> None:
    payload = {"name": fake.word()}

    response = client.post(Endpoints.TOPICS, json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.post(Endpoints.TOPICS, json=payload, headers=get_header())
    assert response.status_code == status.HTTP_201_CREATED


def test_create_topics_multiple_time() -> None:
    payload = {"name": fake.word()}

    response = client.post(Endpoints.TOPICS, json=payload, headers=get_header())
    assert response.status_code == status.HTTP_201_CREATED

    response = client.post(Endpoints.TOPICS, json=payload, headers=get_header())
    assert response.status_code == status.HTTP_201_CREATED
