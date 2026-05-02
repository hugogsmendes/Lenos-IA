from dotenv import load_dotenv
from repository.comment_repository import Comment_Repository
import os
import googleapiclient.discovery
import googleapiclient.errors
from utils.exceptions import BadGateway, BadRequest, NotFound, Forbidden


load_dotenv()

class Comment_Service:

    def __init__(self, repository: Comment_Repository):
        self.repository = repository
        self.api_service_name = "youtube"
        self.api_version = "v3"
        self._api_key = os.getenv("key_youtube")
        self.youtube_service = googleapiclient.discovery.build(self.api_service_name, self.api_version, developerKey = self._api_key)

    async def verify_video_exists (self, video_id: str):

        try:
            request = self.youtube_service.videos().list(
                part = "snippet",
                id = video_id
            )
            
            response = request.execute()
            
            if response.get("pageInfo", {}).get("totalResults", 0) == 0:
                raise NotFound(register = video_id, detail = "não encontrado no YouTube")
            
            return
        
        except googleapiclient.errors.HttpError as e:
            status_code = e.resp.status
            
            if status_code == 404:
                raise NotFound(register = video_id, detail = "não encontrado no Youtube")
            elif status_code == 403:
                raise Forbidden(detail = f"Acesso negado ao YouTube API - Verifique a chave de API")
            elif status_code == 400:
                raise BadRequest(detail = f"Video ID inválido")

        except Exception as e:
            raise BadRequest(detail = f"Erro {str(e)}")

    def get_comments_by_video_id (self, video_id: str):

        try:
            
            request = self.youtube_service.commentThreads().list(
                part="snippet",
                maxResults = 20,
                order = "relevance",
                videoId = video_id
            )

            response = request.execute()
            return response
        
        except googleapiclient.errors.HttpError as e:
            status_code = e.resp.status
            raise BadGateway(detail =f"Erro ao buscar comentários do YouTube (HTTP {status_code}): {e.error_details}")
        
    def processing_comments(self, comments):
        ...