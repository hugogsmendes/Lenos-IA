from src.models.reports import Report
from src.models.analyses import Analysis
from src.utils.schemas import UpdatedReport
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from uuid import UUID


class Report_Repository:

    def __init__(self, session: AsyncSession, cache: Redis):
        self.session = session
        self.cache = cache
        self.cache_key = "reports"
    
    async def create_report (self, analysis_id: UUID):

        new_report = Report(analysis_id = analysis_id)

        self.session.add(new_report)
        await self.session.flush()
        return new_report
      
    async def get_reports_by_user (self, user_id: str) -> tuple[UUID, str, str, str, str]:

        query = (
                select(Report.id, Report.report_title, Analysis.video_url ,Report.report_markdown, Analysis.status)
                 .join(Report.analysis)
                 .filter(Analysis.user_id == user_id)
                 )
        
        result = await self.session.execute(query)

        return result.all()
    
    async def get_report_by_id (self, report_id: UUID) -> Report | None:

        query = select(Report).filter(Report.id == report_id)

        result = await self.session.execute(query)

        return result.scalar_one_or_none()
    
    async def update_report (self, schema: UpdatedReport, report: Report, cache_key: str) -> None:
        
        report.report_title = schema.new_title
        await self.session.commit()
        await self.cache.delete(cache_key)
        await self.session.refresh(report)

    async def update_report_done_by_id (self, report_id: UUID, prompt: str, title: str, markdown: str) -> None:

        query = update(Report).filter(Report.id == report_id).values(prompt = prompt,
                                                                     report_title = title,
                                                                     report_markdown = markdown)
        await self.session.execute(query)

    async def update_report_failed_by_id (self, report_id: UUID) -> None:

        query = update(Report).filter(Report.id == report_id).values(prompt = "failed",
                                                                     report_title = "failed",
                                                                     report_markdown = "failed")
        await self.session.execute(query)

    async def report_done_count_by_user_id (self, user_id: str):
        
        query = (select(func.count()).select_from(Report)
            .join(Report.analysis)
            .filter(Analysis.user_id == user_id, Analysis.status == "done"))

        result = await self.session.execute(query)

        return result.scalar()
