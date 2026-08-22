from fastapi import APIRouter, Depends, status, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from src.app.main import limiter
from src.utils.dependencies import get_current_user
from src.utils.schemas import GenerateReport, UpdatedReport, MessageError, RateLimitError, ResponseReportCreate, ResponseReport
from src.service.report_service import Report_Service
from src.utils.dependencies import get_report_service
import io
from uuid import UUID

report_router = APIRouter(prefix = "/v1/user", tags = ["report"])

generete_report_responses = {
    201: {"model": ResponseReportCreate, "description": "Relatório criado"},
    400: {"model": MessageError, "description": "URL vídeo inválida, Limite de relatório atingido, Relatório já gerado ou Conta Youtube não conectada"},
    403: {"model": MessageError, "description": "Sem permissão"},
    404: {"model": MessageError, "description": "Vídeo não encontrado no YouTube"},
    429: {"model": RateLimitError, "description": "Limite de requisição"},
    502: {"model": MessageError, "description": "Serviço indisponível"}
}

report_by_id_responses = {
    200: {"model": ResponseReport, "description": "Relatório listado"},
    400: {"model": MessageError, "description": "Relatório não encontrado ou não pertence ao usuário"},
    403: {"model": MessageError, "description": "Sem permissão"},
    429: {"model": RateLimitError, "description": "Limite de requisição"},
    502: {"model": MessageError, "description": "Serviço indisponível"}
}

report_pdf_by_id_responses = {
    200: {
        "description": "Arquivo PDF baixado",
        "content": {
            "application/pdf": {
                "schema": {
                    "type": "string",
                    "format": "binary"
                }
            }
        }
    },
    400: {"model": MessageError, "description": "Relatório não pertence ao usuário"},
    403: {"model": MessageError, "description": "Sem permissão"},
    429: {"model": RateLimitError, "description": "Limite de requisição"},
    502: {"model": MessageError, "description": "Serviço indisponível"}
}

list_reports_responses = {
    200: {"model": list[ResponseReport], "description": "Relatórios listados"},
    403: {"model": MessageError, "description": "Sem permissão"},
    429: {"model": RateLimitError, "description": "Limite de requisição"},
    502: {"model": MessageError, "description": "Serviço indisponível"}
}

update_report_responses = {
    204: {"model": None, "description": "Relatório atualizado"},
    400: {"model": MessageError, "description": "Relatório não pertence ao usuário"},
    403: {"model": MessageError, "description": "Sem permissão"},
    429: {"model": RateLimitError, "description": "Limite de requisição"},
    502: {"model": MessageError, "description": "Serviço indisponível"}
}

delete_report_responses = {
    204: {"model": None, "description": "Relatório deletado"},
    400: {"model": MessageError, "description": "Relatório não pertence ao usuário"},
    403: {"model": MessageError, "description": "Sem permissão"},
    429: {"model": RateLimitError, "description": "Limite de requisição"},
    502: {"model": MessageError, "description": "Serviço indisponível"}
}

@report_router.post(path = "/generate-report", 
                    responses = generete_report_responses,
                    status_code = status.HTTP_201_CREATED)
@limiter.limit("1/minute")
async def create_report (request: Request, body: GenerateReport, background_tasks: BackgroundTasks,
                        service: Report_Service = Depends(get_report_service), current_user: dict = Depends(get_current_user)):
    
    return await service.create_report(body, current_user.get("id"), background_tasks)

@report_router.get(path = "/report/{id}", 
                   responses = report_by_id_responses,
                   status_code = status.HTTP_200_OK)
@limiter.limit("10/minute")
async def get_report_by_id (request: Request, id: UUID, service: Report_Service = Depends(get_report_service), current_user: dict = Depends(get_current_user)):
    return await service.get_report_by_id(id, current_user.get("id"))

@report_router.get(path = "/report/{id}/pdf", 
                   responses = report_pdf_by_id_responses,
                   status_code = status.HTTP_200_OK)
@limiter.limit("10/minute")
async def get_report_pdf_by_id (request: Request, id: UUID,
                                service: Report_Service = Depends(get_report_service), current_user: dict = Depends(get_current_user)):
    
    pdf_bytes, filename = await service.get_report_pdf_by_id(id, current_user.get("id"))

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type = "application/pdf",
        headers = {"Content-Disposition": f"attachment; filename={filename}.pdf"}
    )

@report_router.get(path = "/reports",
                   responses = list_reports_responses,
                   status_code = status.HTTP_200_OK)
@limiter.limit("10/minute")
async def get_reports_by_user (request: Request, service: Report_Service = Depends(get_report_service), current_user: dict = Depends(get_current_user)):
    return await service.get_reports_by_user(current_user.get("id"))

@report_router.put(path = "/report/{id}",
                   responses = update_report_responses,
                   status_code = status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def update_report(request: Request, id: UUID, body: UpdatedReport, service: Report_Service = Depends(get_report_service), current_user: dict = Depends(get_current_user)):
    return await service.update_report(id, body, current_user.get("id"))

@report_router.delete(path = "/report/{id}",
                      responses = delete_report_responses,
                      status_code = status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_report(request: Request, id: UUID, service: Report_Service = Depends(get_report_service), current_user: dict = Depends(get_current_user)):
    return await service.delete_report(id, current_user.get("id"))