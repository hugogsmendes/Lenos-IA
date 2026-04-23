from sqlalchemy.ext.asyncio import AsyncSession
from models.analyses import Analysis
from sqlalchemy import select
from models.reports import Report
from uuid import UUID


class Analysis_Repository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_analysis(self, user_id: UUID, video_url, youtube_video_id) -> Analysis:
        
        new_analysis = Analysis(user_id = user_id,
                               video_url = video_url,
                               youtube_video_id = youtube_video_id)
        
        self.session.add(new_analysis)
        await self.session.commit()
        await self.session.refresh(new_analysis)

        return new_analysis
    
    async def get_analysis_by_report_id (self, report_id: UUID) -> Analysis:

        query = select(Analysis).join(Analysis.report).filter(Report.id == report_id)

        result = await self.session.execute(query)

        return result.scalar_one_or_none()
