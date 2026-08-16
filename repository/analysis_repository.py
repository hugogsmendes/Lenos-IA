from sqlalchemy.ext.asyncio import AsyncSession
from models.analyses import Analysis
from sqlalchemy import select, update
from models.reports import Report
from uuid import UUID

class Analysis_Repository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_analysis(self, user_id: str, video_url: str, youtube_video_id: str):
        
        new_analysis = Analysis(user_id = user_id,
                               video_url = video_url,
                               youtube_video_id = youtube_video_id)
        
        self.session.add(new_analysis)
        await self.session.flush()
        return new_analysis
    
    async def get_analysis_by_report_id (self, report_id: UUID, user_id: str) -> Analysis | None:

        query = select(Analysis).join(Analysis.report).filter(Report.id == report_id, Analysis.user_id == user_id)

        result = await self.session.execute(query)

        return result.scalar_one_or_none()
    
    async def get_analysis_by_youtube_video_id (self, youtube_video_id: str, user_id: str) -> str:

        query = (select(Analysis.youtube_video_id).filter(Analysis.youtube_video_id == youtube_video_id,
                                                        Analysis.user_id == user_id, Analysis.status == "done"))

        result = await self.session.execute(query)

        return result.scalar_one_or_none()
    
    async def delete_analysis (self, analysis: Analysis) -> None:

        await self.session.delete(analysis)
        await self.session.commit()

    async def update_analysis_done_by_id (self, analysis_id: UUID) -> None:

        query = update(Analysis).filter(Analysis.id == analysis_id).values(status = "done")
        await self.session.execute(query)
        
    async def update_analysis_failed_by_id (self, analysis_id: UUID) -> None:

        query = update(Analysis).filter(Analysis.id == analysis_id).values(status = "failed")
        await self.session.execute(query)

