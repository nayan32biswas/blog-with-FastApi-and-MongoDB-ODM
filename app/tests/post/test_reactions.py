from faker import Faker
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.post.models import Reaction
from app.tests.endpoints import Endpoints
from app.tests.post.helper import create_public_post
from app.tests.utils import get_header, get_user

client = TestClient(app)
fake = Faker()


def test_reactions() -> None:
    user = get_user()
    post = create_public_post(user.id)

    response = client.post(
        Endpoints.REACTIONS.format(slug=post.slug), headers=get_header()
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert Reaction.exists({"post_id": post.id, "user_ids": user.id}) is True

    # Delete reaction
    response = client.delete(
        Endpoints.REACTIONS.format(slug=post.slug), headers=get_header()
    )
    assert response.status_code == status.HTTP_200_OK
    assert Reaction.exists({"post_id": post.id, "user_ids": user.id}) is False


def test_reactions_auth() -> None:
    user = get_user()
    post = create_public_post(user.id)

    response = client.post(Endpoints.REACTIONS.format(slug=post.slug))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.delete(Endpoints.REACTIONS.format(slug=post.slug))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
