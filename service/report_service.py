from repository.report_repository import Report_Repository


class Report_Service:

    def __init__(self, repository: Report_Repository):
        self.repository = repository