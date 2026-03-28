from sqlalchemy.ext.asyncio import AsyncSession


class Report_Repository:

    def __init__(self, session: AsyncSession):
        self.session = session