from fastapi import FastAPI

app = FastAPI(
    title = "Lenos IA",
    version = "1.0.0"
)

from api.routes.user_routes import user_router
from api.routes.question_routes import question_router
from api.routes.answer_routes import answer_router

app.include_router(user_router)
app.include_router(question_router)
app.include_router(answer_router)
