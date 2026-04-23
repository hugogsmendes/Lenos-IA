from sqlalchemy.ext.asyncio import AsyncSession
from models.analyses import Analyse
from uuid import UUID


class Analyse_Repository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_analysis(self, user_id: UUID, video_url, youtube_video_id) -> Analyse:
        
        new_analysis = Analyse(user_id = user_id,
                               video_url = video_url,
                               youtube_video_id = youtube_video_id)
        
        self.session.add(new_analysis)
        await self.session.commit()
        await self.session.refresh(new_analysis)

        return new_analysis
