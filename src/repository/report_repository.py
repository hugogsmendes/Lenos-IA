from src.models.reports import Report
from src.models.analyses import Analysis
from src.utils.schemas import UpdatedReport
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from uuid import UUID
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

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
      
    async def get_reports_by_user (self, user_id: str):

        query = (
            select(Report.id, Report.report_title, Analysis.video_url ,Report.report_markdown, Analysis.status, 
                    Report.processed_comments, Report.processed_comments_positive, Report.processed_comments_negative,
                    Report.created_at)
            .join(Report.analysis)
            .filter(
                Analysis.user_id == user_id,
                Analysis.deleted_at.is_(None))
            )

        stats_query = (
            select(
                func.count(Report.id).label("reports_count"),
                func.coalesce(
                    func.sum(Report.processed_comments), 0
                ).label("comments_processed"),
                func.coalesce(
                    func.sum(Report.processed_comments_positive), 0
                ).label("comments_positive"),
                func.coalesce(
                    func.sum(Report.processed_comments_negative), 0
                ).label("comments_negative"),
            )
            .select_from(Report)
            .join(Report.analysis)
            .filter(
                Analysis.user_id == user_id,
                Analysis.deleted_at.is_(None),
            )
        )
        
        reports = await self.session.execute(query)
        stats = await self.session.execute(stats_query)

        return reports.all(), stats.one()
    
    async def get_report_by_id (self, report_id: UUID) -> Report | None:

        query = select(Report).join(Report.analysis).filter(Report.id == report_id, Analysis.deleted_at.is_(None))

        result = await self.session.execute(query)

        return result.scalar_one_or_none()
    
    async def update_report (self, schema: UpdatedReport, report: Report, cache_key: str) -> None:
        
        report.report_title = schema.new_title
        await self.session.commit()
        await self.cache.delete(cache_key)
        await self.session.refresh(report)

    async def update_report_done_by_id (self, report_id: UUID, prompt: str, title: str, markdown: str, processed_comments: int, 
                                        processed_comments_positive: int, processed_comments_negative: int) -> None:

        query = update(Report).filter(Report.id == report_id).values(prompt = prompt,
                                                                     report_title = title,
                                                                     report_markdown = markdown,
                                                                     processed_comments = processed_comments,
                                                                     processed_comments_positive = processed_comments_positive,
                                                                     processed_comments_negative = processed_comments_negative)
        await self.session.execute(query)

    async def update_report_failed_by_id (self, report_id: UUID) -> None:

        query = update(Report).filter(Report.id == report_id).values(prompt = "failed",
                                                                     report_title = "failed",
                                                                     report_markdown = "failed")
        await self.session.execute(query)

    async def report_done_count_by_user_id (self, user_id: str):
        
        now = datetime.now(timezone.utc)

        start_of_month = now.replace(
            day = 1,
            hour = 0,
            minute = 0,
            second = 0,
            microsecond = 0,
        )

        start_of_next_month = start_of_month + relativedelta(months = 1)

        query = (
            select(
                func.count(Report.id).label("reports_used"),
                func.coalesce(
                    func.sum(Report.processed_comments), 0
                ).label("comments_processed"),
            )
            .select_from(Report)
            .join(Report.analysis)
            .filter(
                Analysis.user_id == user_id,
                Analysis.status == "done",
                Report.created_at >= start_of_month,
                Report.created_at < start_of_next_month,
            )
        )

        result = await self.session.execute(query)

        return result.one()
