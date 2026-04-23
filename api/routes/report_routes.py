from fastapi import APIRouter, Depends, status, Response, Request
from app.main import limiter
from utils.dependencies import get_current_user
from utils.schemas import GenerateReport
from service.report_service import Report_Service
from utils.dependencies import get_report_service
from uuid import UUID

report_router = APIRouter(prefix = "/v1", tags = ["report"])

@report_router.post(path = "/user/generate_report", status_code = status.HTTP_201_CREATED)
@limiter.limit("1/minute")
async def create_report (request: Request, body: GenerateReport, service: Report_Service = Depends(get_report_service),
                        current_user: dict = Depends(get_current_user)):
    
    return await service.create_report(body, current_user.get("id"))

@report_router.get(path = "/user/report/{id}", status_code = status.HTTP_200_OK)
async def get_report_by_id (id: UUID, service: Report_Service = Depends(get_report_service), current_user: dict = Depends(get_current_user)):
    return await service.get_report_by_id(id)

@report_router.get(path = "/user/reports", status_code = status.HTTP_200_OK)
async def get_reports_by_user (service: Report_Service = Depends(get_report_service), current_user: dict = Depends(get_current_user)):
    return await service.get_reports_by_user(current_user.get("id"))

