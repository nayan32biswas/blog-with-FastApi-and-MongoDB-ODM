import logging
import os
from typing import Any

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import FileResponse
from mongodb_odm.connection import get_client

from app.base.config import MEDIA_ROOT
from app.base.exceptions import CustomException, ExType
from app.base.utils.file import save_file
from app.user.dependencies import get_authenticated_user, get_authenticated_user_or_none
from app.user.models import User

router = APIRouter()
logger = logging.getLogger(__name__)


def is_database_stable() -> bool:
    try:
        get_client().admin.command("ping")

        return True
    except Exception as e:
        logger.error(f"Mongo Server not available. Error: {e}")
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ExType.INTERNAL_SERVER_ERROR,
            detail="Database is not stable",
        ) from e


@router.get("/")
async def home_page() -> Any:
    is_database_stable()

    return {"message": "Server alive"}


@router.get("/health")
def health_check() -> Any:
    is_database_stable()

    return {"status": "ok"}


@router.post("/api/v1/upload-image", status_code=status.HTTP_201_CREATED)
async def create_upload_image(
    image: UploadFile = File(...),
    _: User = Depends(get_authenticated_user),
) -> Any:
    image_path = save_file(image, root_folder="image")
    return {"image_path": image_path}


@router.get("/media/{file_path:path}")
async def get_image(
    file_path: str,
    _: User | None = Depends(get_authenticated_user_or_none),
) -> Any:
    file_path = f"{MEDIA_ROOT}/{file_path}"

    if os.path.isfile(file_path):
        return FileResponse(file_path)
    else:
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ExType.OBJECT_NOT_FOUND,
            detail="file not found",
        )
