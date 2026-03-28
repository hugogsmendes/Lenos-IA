from sqlalchemy.ext.asyncio import AsyncSession


class Analyse_Repository:

    def __init__(self, session: AsyncSession):
        self.session = session