from fastapi import FastAPI

app = FastAPI()

from api.routes.user_routes import user_router

app.include_router(user_router)