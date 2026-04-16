from fastapi import APIRouter, Depends, status, Response, Request
from app.main import limiter
from utils.dependencies import get_current_user
from utils.schemas import GenerateReport
from service.report_service import Report_Service
from utils.dependencies import get_report_service

report_router = APIRouter(prefix = "/v1", tags = ["report"])

@report_router.post(path = "/user/generate_report", status_code = status.HTTP_201_CREATED)
@limiter.limit("1/minute")
async def create_report (request: Request, body: GenerateReport, service: Report_Service = Depends(get_report_service),
                        current_user: dict = Depends(get_current_user)):
    
    return await service.create_report(body, current_user.get("id"))

@report_router.get(path = "/user/report/{id}", status_code = status.HTTP_200_OK)
async def list_report (id, service: Report_Service = Depends(get_report_service), current_user: dict = Depends(get_current_user)):
    return await service.list_report(id)

