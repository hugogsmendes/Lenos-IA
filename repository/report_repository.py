from sqlalchemy.ext.asyncio import AsyncSession
from models.reports import Report
from models.analyses import Analysis
from sqlalchemy import select
from uuid import UUID


class Report_Repository:

    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_report (self, analysis_id: UUID) -> Report:

        new_report = Report(analysis_id = analysis_id)

        self.session.add(new_report)
        await self.session.commit()
        await self.session.refresh(new_report)

        return new_report
    
    async def get_report_by_id (self, report_id: UUID) -> tuple:
        
        query = (
                select(Report.id, Report.report_title, Report.report_markdown, Analysis.status)
                 .join(Report.analysis)
                 .filter(Report.id == report_id)
                 )
        
        result = await self.session.execute(query)

        return result.all()
    
    async def get_reports_by_user (self, user_id: UUID) -> tuple:

        query = (
                select(Report.id, Report.report_title, Report.report_markdown, Analysis.status)
                 .join(Report.analysis)
                 .filter(Analysis.user_id == user_id)
                 )
        
        result = await self.session.execute(query)

        return result.all()