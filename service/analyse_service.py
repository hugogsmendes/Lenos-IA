from repository.analyses_repository import Analyse_Repository


class Analyse_Service:

    def __init__(self, repository: Analyse_Repository):
        self.repository = repository