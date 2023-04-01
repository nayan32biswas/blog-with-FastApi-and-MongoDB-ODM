import logging
import time

from fastapi import Request, Response

from .config import DEBUG

logger = logging.getLogger(__name__)


async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.critical(f"""Unhandled Error:{e}""")
        if DEBUG:
            raise e
        else:
            return Response("Internal server error", status_code=500)
