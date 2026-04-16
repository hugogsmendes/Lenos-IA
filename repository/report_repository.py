from sqlalchemy.ext.asyncio import AsyncSession
from models.reports import Report
from models.analyses import Analyse
from sqlalchemy import select


class Report_Repository:

    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_report (self, analysis_id) -> Report:

        new_report = Report(analysis_id = analysis_id)

        self.session.add(new_report)
        await self.session.commit()
        await self.session.refresh(new_report)

        return new_report
    
    async def list_report (self, report_id) -> tuple:
        
        query = (
                select(Report.report_title, Report.report_markdown, Analyse.status)
                 .join(Report.analysis)
                 .filter(Report.id == report_id)
                 )
        
        result = await self.session.execute(query)

        return result.all()
    
    async def get_report_by_id (self, report_id):

        query = select(Report.id).filter(Report.id == report_id)

        result = await self.session.execute(query)

        return result.scalar_one_or_none()