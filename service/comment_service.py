from dotenv import load_dotenv
from repository.comment_repository import Comment_Repository
import os


load_dotenv()

class Comment_Service:

    def __init__(self, repository: Comment_Repository):
        self.repository = repository
        self.api_service_name = "youtube"
        self.version = "v3"
        self._api_key = os.getenv("key_youtube")

    