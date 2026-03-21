from repository.question_repository import Question_Repository

class Question_Service:

    def __init__(self, repository: Question_Repository):
        self.repository = repository

    async def create_question (self, description: str):

        return await self.repository.create_question(description)