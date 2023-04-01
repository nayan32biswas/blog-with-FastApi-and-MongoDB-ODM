import logging

from fastapi import APIRouter, Depends, File, UploadFile

from app.user.dependencies import get_authenticated_user
from app.user.models import User

from .utils.file import save_file

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/api/v1/upload-image")
async def create_upload_image(
    image: UploadFile = File(...),
    _: User = Depends(get_authenticated_user),
):
    image_path = save_file(image, root_folder="image")
    return image_path
