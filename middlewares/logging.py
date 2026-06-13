import time
import logging

from fastapi import Request

logger = logging.getLogger("api")


async def logging_middleware(request: Request, call_next):

    start = time.perf_counter()

    response = await call_next(request)

    duration = time.perf_counter() - start

    logger.info(
        "method=%s path=%s status=%s duration=%.4fs",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )

    return response