from fastapi import APIRouter, Depends, status, Response, Request
from utils.dependencies import get_current_user
from utils.schemas import GenerateReport

report_router = APIRouter(prefix = "/v1", tags = ["report"], dependencies = [Depends(get_current_user)])

@report_router.post(path = "user/generate_report", status_code = status.HTTP_201_CREATED)
async def create_report (body: GenerateReport):
    ...

