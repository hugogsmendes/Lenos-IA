from repository.user_repository import User_Repository

class User_Service:

    def __init__(self, repository: User_Repository):
        self.repository = repository