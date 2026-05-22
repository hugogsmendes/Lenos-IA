from sqlalchemy.ext.asyncio import AsyncSession
from models.reports import Report
from models.analyses import Analysis
from sqlalchemy import select, func
from uuid import UUID
from utils.schemas import UpdatedReport


class Report_Repository:

    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_report (self, analysis_id: UUID) -> Report:

        new_report = Report(analysis_id = analysis_id)

        self.session.add(new_report)
        await self.session.commit()
        await self.session.refresh(new_report)

        return new_report
    
    async def get_report_by_id (self, report_id: UUID) -> tuple[UUID, str, str, str, str]:
        
        query = (
                select(Report.id, Report.report_title, Analysis.video_url, Report.report_markdown, Analysis.status)
                 .join(Report.analysis)
                 .filter(Report.id == report_id)
                 )
        
        result = await self.session.execute(query)

        return result.all()
    
    async def get_reports_by_user (self, user_id: UUID) -> tuple[UUID, str, str, str, str]:

        query = (
                select(Report.id, Report.report_title, Analysis.video_url ,Report.report_markdown, Analysis.status)
                 .join(Report.analysis)
                 .filter(Analysis.user_id == user_id)
                 )
        
        result = await self.session.execute(query)

        return result.all()
    
    async def get_report (self, report_id: UUID) -> Report:

        query = select(Report).filter(Report.id == report_id)

        result = await self.session.execute(query)

        return result.scalar_one_or_none()
    
    async def update_report (self, schema: UpdatedReport, report: Report) -> None:
        
        report.report_title = schema.title
        await self.session.commit()
        await self.session.refresh(report)

    async def update_report_done (self, report: Report, prompt: str, title: str, markdown: str) -> None:

        report.prompt = prompt
        report.report_title = title
        report.report_markdown = markdown
        await self.session.commit()
        await self.session.refresh(report)

    async def update_report_failed (self, report: Report) -> None:
        report.prompt = "failed"
        report.report_title = "failed"
        report.report_markdown = "failed"
        await self.session.commit()
        await self.session.refresh(report)

    async def report_count (self, user_id: UUID):
        
        query = (select(func.count()).select_from(Report)
            .join(Report.analysis)
            .filter(Analysis.user_id == user_id))

        result = await self.session.execute(query)

        return result.scalar()
