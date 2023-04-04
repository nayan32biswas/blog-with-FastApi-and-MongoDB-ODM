from fastapi import status
from fastapi.testclient import TestClient

from app.main import app

from .config import get_header, get_test_file_path, init_config  # noqa

client = TestClient(app)

NEW_USERNAME = "username-exists"
NEW_PASS = "new-pass"
NEW_FULL_NAME = "Full Name"


def test_file_upload() -> None:
    image_path = f"{get_test_file_path()}/atom.jpg"

    with open(image_path, "rb") as f:
        response = client.post(
            "/api/v1/upload-image", files={"image": f}, headers=get_header()
        )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json().get("image_path") is not None
