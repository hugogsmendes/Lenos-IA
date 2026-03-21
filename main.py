from fastapi import FastAPI

app = FastAPI()

from api.routes.user_routes import user_router
from api.routes.question_routes import question_router

app.include_router(user_router)
app.include_router(question_router)
