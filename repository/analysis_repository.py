from sqlalchemy.ext.asyncio import AsyncSession
from models.analyses import Analysis
from sqlalchemy import select
from models.reports import Report
from uuid import UUID

class Analysis_Repository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_analysis(self, user_id: UUID, video_url: str, youtube_video_id: str) -> Analysis:
        
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
    
    async def get_analysis_by_youtube_video_id (self, youtube_video_id: str, user_id: UUID) -> str:

        query = (select(Analysis.youtube_video_id).filter(Analysis.youtube_video_id == youtube_video_id,
                                                        Analysis.user_id == user_id, Analysis.status == "done"))

        result = await self.session.execute(query)

        return result.scalar_one_or_none()
    
    async def delete_analysis (self, analysis: Analysis) -> None:

        await self.session.delete(analysis)
        await self.session.commit()

    async def update_analysis_failed (self, analysis: Analysis) -> None:

        analysis.status = "failed"
        await self.session.commit()
        await self.session.refresh(analysis)

    async def update_analysis_done (self, analysis: Analysis) -> None:

        analysis.status = "done"
        await self.session.commit()
        await self.session.refresh(analysis)

