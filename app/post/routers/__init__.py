from fastapi import APIRouter

from . import comments, posts

router = APIRouter()

router.include_router(posts.router)
router.include_router(comments.router)
