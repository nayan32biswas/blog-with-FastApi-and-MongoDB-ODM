from logging.config import dictConfig
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mongodb_odm import connect, disconnect
from starlette.middleware.base import BaseHTTPMiddleware

from app.base import config
from app.base import routers as base_routers
from app.base.exception_handler import UnicornException, unicorn_exception_handler
from app.base.middleware import add_process_time_header, catch_exceptions_middleware
from app.post import routers as post_routers
from app.user import routers as user_routers

dictConfig(config.log_config)
app: Any = FastAPI(debug=config.DEBUG)


@app.on_event("startup")
async def startup_db_client():
    connect(config.MONGO_HOST)


@app.on_event("shutdown")
async def shutdown_db_client():
    disconnect()


app.include_router(base_routers.router, tags=["base"])
app.include_router(post_routers.router, tags=["post"])
app.include_router(user_routers.router, tags=["user"])


if config.DEBUG is True:
    app.add_middleware(BaseHTTPMiddleware, dispatch=add_process_time_header)

# Exception handler
app.add_exception_handler(UnicornException, unicorn_exception_handler)

# Add middleware
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
    from app.base.tools.cli import cli_app

    connect(config.MONGO_HOST)
    cli_app()
    disconnect()
