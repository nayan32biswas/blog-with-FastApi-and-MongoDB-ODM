from logging.config import dictConfig
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mongodb_odm import connect, disconnect
from starlette.middleware.base import BaseHTTPMiddleware

from app.base import config
from app.base import routers as base_routers
from app.base.exception_handler import (
    handle_custom_exception,
    unicorn_exception_handler,
)
from app.base.exceptions import CustomException, UnicornException
from app.base.middleware import catch_exceptions_middleware
from app.post import routers as post_routers
from app.user import routers as user_routers

dictConfig(config.log_config)
app: Any = FastAPI(debug=config.DEBUG, lifespan=config.lifespan)

app.include_router(base_routers.router, tags=["base"])
app.include_router(post_routers.router, tags=["post"])
app.include_router(user_routers.router, tags=["user"])


# Exception handler
app.add_exception_handler(UnicornException, unicorn_exception_handler)
app.add_exception_handler(CustomException, handle_custom_exception)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(BaseHTTPMiddleware, dispatch=catch_exceptions_middleware)


if __name__ == "__main__":
    """CLI"""
    from cli.main import app as cli_app

    connect(config.MONGO_URL)
    cli_app()
    disconnect()
