from fastapi import APIRouter, Depends, status, Response, Request
from app.main import limiter
from utils.dependencies import get_current_user
from utils.schemas import GenerateReport, UpdatedReport
from service.report_service import Report_Service
from utils.dependencies import get_report_service
from uuid import UUID

report_router = APIRouter(prefix = "/v1/user", tags = ["report"])

@report_router.post(path = "/generate_report", status_code = status.HTTP_201_CREATED)
@limiter.limit("1/minute")
async def create_report (request: Request, body: GenerateReport, service: Report_Service = Depends(get_report_service),
                        current_user: dict = Depends(get_current_user)):
    
    return await service.create_report(body, current_user.get("id"))

@report_router.get(path = "/report/{id}", status_code = status.HTTP_200_OK)
@limiter.limit("10/minute")
async def get_report_by_id (request: Request, id: UUID, service: Report_Service = Depends(get_report_service), current_user: dict = Depends(get_current_user)):
    return await service.get_report_by_id(id, current_user.get("id"))

@report_router.get(path = "/reports", status_code = status.HTTP_200_OK)
@limiter.limit("10/minute")
async def get_reports_by_user (request: Request, service: Report_Service = Depends(get_report_service), current_user: dict = Depends(get_current_user)):
    return await service.get_reports_by_user(current_user.get("id"))

@report_router.put(path = "/update_report", status_code = status.HTTP_204_NO_CONTENT)
async def update_report(body: UpdatedReport, service: Report_Service = Depends(get_report_service), current_user: dict = Depends(get_current_user)):
    return await service.update_report(body, current_user.get("id"))

@report_router.delete(path = "/delete_report/{id}", status_code = status.HTTP_200_OK)
async def delete_report(id: UUID, service: Report_Service = Depends(get_report_service), current_user: dict = Depends(get_current_user)):
    await service.delete_report(id, current_user.get("id"))
    return {"message": "Relatório deletado com sucesso"}