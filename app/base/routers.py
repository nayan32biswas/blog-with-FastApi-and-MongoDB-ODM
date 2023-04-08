import logging
from typing import Any

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.user.dependencies import get_authenticated_user
from app.user.models import User

from .utils.file import save_file

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/api/v1/upload-image", status_code=status.HTTP_201_CREATED)
async def create_upload_image(
    image: UploadFile = File(...),
    _: User = Depends(get_authenticated_user),
) -> Any:
    image_path = save_file(image, root_folder="image")
    return {"image_path": image_path}
