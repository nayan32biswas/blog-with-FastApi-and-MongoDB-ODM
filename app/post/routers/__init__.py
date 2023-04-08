from fastapi import APIRouter

from . import comments, posts, reactions

router = APIRouter()

router.include_router(posts.router)
router.include_router(comments.router)
router.include_router(reactions.router)
