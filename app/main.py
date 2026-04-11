from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func = get_remote_address)

app = FastAPI(
    title = "Lenos IA",
    version = "1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

from api.routes.user_routes import user_router
from api.routes.question_routes import question_router
from api.routes.answer_routes import answer_router

app.include_router(user_router)
app.include_router(question_router)
app.include_router(answer_router)
