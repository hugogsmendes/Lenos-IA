from dotenv import load_dotenv
from repository.comment_repository import Comment_Repository
import os
import re
import googleapiclient.discovery
import googleapiclient.errors
from utils.exceptions import BadGateway, BadRequest, NotFound, Forbidden
from fastapi import HTTPException
import asyncio
from utils.logging import get_logger

logger = get_logger("comment_service")


load_dotenv()

_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F1E6-\U0001F1FF"
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "\uFE0F"
    "\u200D"
    "]+",
    flags = re.UNICODE,
)


class Comment_Service:

    def __init__(self, repository: Comment_Repository):
        self.repository = repository
        self.api_service_name = "youtube"
        self.api_version = "v3"
        self._api_key = os.getenv("key_youtube")
        self.youtube_service = googleapiclient.discovery.build(self.api_service_name, self.api_version, developerKey = self._api_key)

    async def verify_video_exists (self, video_id: str):

        try:
            logger.info("Verifying existence of video %s on YouTube", video_id)
            request = self.youtube_service.videos().list(
                part = "snippet",
                id = video_id
            )
            
            response = await asyncio.to_thread(request.execute)
            
            if response.get("pageInfo", {}).get("totalResults", 0) == 0:
                logger.warning("Video %s not found on YouTube", video_id)
                raise NotFound(register = video_id, detail = "não encontrado no YouTube")
            
            logger.info("Video %s verified successfully", video_id)
            return
        
        except googleapiclient.errors.HttpError as e:
            status_code = e.resp.status
            logger.warning("YouTube API error (HTTP %s) verifying video %s: %s", status_code, video_id, str(e))
            
            if status_code == 404:
                raise NotFound(register = video_id, detail = "não encontrado no Youtube")
            elif status_code == 403:
                raise Forbidden(detail = f"Acesso negado ao YouTube API - Verifique a chave de API")
            elif status_code == 400:
                raise BadRequest(detail = f"Video ID inválido")

        except Exception as e:
            logger.error("Unexpected error verifying video %s: %s", video_id, str(e), exc_info=True)
            raise BadRequest(detail = f"Erro {str(e)}")

    async def get_comments_by_video_id (self, video_id: str, max_comments: int = 200):

        try:
            logger.info("Fetching up to %s comments for video %s", max_comments, video_id)
            all_items = []
            next_page_token = None
            
            while len(all_items) < max_comments:
                request = self.youtube_service.commentThreads().list(
                    part = "snippet",
                    maxResults = min(100, max_comments - len(all_items)),
                    order = "relevance",
                    videoId = video_id,
                    pageToken = next_page_token
                )

                response = await asyncio.to_thread(request.execute)
                items = response.get("items", [])
                
                if not items:
                    break
                
                all_items.extend(items)
                
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break
            
            logger.info("Fetched %s comments for video %s", len(all_items), video_id)
            return {"items": all_items[:max_comments], "pageInfo": response.get("pageInfo", {})}
        
        except googleapiclient.errors.HttpError as e:
            status_code = e.resp.status
            logger.error("YouTube API error (HTTP %s) fetching comments for video %s: %s", status_code, video_id, str(e.error_details))
            return
        
    def processing_comments(self, comments: dict):
        try:
            logger.info("Processing comments (cleaning emojis and whitespace)")
            items = comments.get("items", []) if isinstance(comments, dict) else comments

            processed_comments = []

            for item in items:
                snippet = item.get("snippet", {})
                top_level_comment = snippet.get("topLevelComment", {})
                comment_snippet = top_level_comment.get("snippet", {})
                text = comment_snippet.get("textOriginal")

                cleaned_text = self._clean_comment_text(text)

                if cleaned_text:
                    processed_comments.append(cleaned_text)

            logger.info("Processed %s comments successfully", len(processed_comments))
            return processed_comments

        except Exception as e:
            logger.error("Unexpected error in background task processing comments: %s", str(e), exc_info=True)
            return

    def _clean_comment_text(self, text: str):
        if not text:
            return None

        cleaned_text = _EMOJI_PATTERN.sub("", text)
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

        if not cleaned_text:
            return None

        if not any(character.isalnum() for character in cleaned_text):
            return None

        return cleaned_text