from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from utils.logging import configure_logging, get_logger
from middlewares.logging import logging_middleware
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

configure_logging()
logger = get_logger("app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Lenos IA API...")
    yield
    logger.info("Shutting down Lenos IA API...")

limiter = Limiter(key_func = get_remote_address)

app = FastAPI(
    title = "Lenos IA",
    version = "1.0.0",
    lifespan = lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["https://api.lenos-ia.com.br", "https://app.lenos-ia.com.br", "http://localhost:5173"],    
    allow_credentials = True,     
    allow_methods = ["*"],      
    allow_headers = ["*"],     
)

app.middleware("http")(logging_middleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

from api.routes.user_routes import user_router
from api.routes.question_routes import question_router
from api.routes.answer_routes import answer_router
from api.routes.report_routes import report_router

app.include_router(user_router)
app.include_router(question_router)
app.include_router(answer_router)
app.include_router(report_router)
