from fastapi import status
from httpx import AsyncClient

from app.tests.utils import get_header, get_test_file_path

NEW_USERNAME = "username-exists"
NEW_PASS = "new-pass"
NEW_FULL_NAME = "Full Name"


async def test_file_upload_and_get(async_client: AsyncClient) -> None:
    image_path = f"{get_test_file_path()}/atom.jpg"

    with open(image_path, "rb") as f:
        response = await async_client.post(
            "/api/v1/upload-image", files={"image": f}, headers=await get_header()
        )
    assert response.status_code == status.HTTP_201_CREATED

    image_path = response.json().get("image_path")

    assert image_path is not None

    response = await async_client.get(image_path)
    assert response.status_code == status.HTTP_200_OK
