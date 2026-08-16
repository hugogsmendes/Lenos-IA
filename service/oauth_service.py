from repository.oauth_repository import Oauth_Repository
from utils.exceptions import BadGateway, BadRequest, NotFound
from fastapi import HTTPException
from settings.config import Settings
import httpx
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
import asyncio
from utils.logging import get_logger

logger = get_logger("oauth_service")

settings = Settings()

CLIENT_SECRET = settings.CLIENT_SECRET
CLIENT_ID = settings.CLIENT_ID
REDIRECT_URI = settings.REDIRECT_URI
TOKEN_URI = settings.TOKEN_URI

class Oauth_Service:

    def __init__(self, repository: Oauth_Repository):
        self.repository = repository
        self.api_service_name = "youtube"
        self.api_version = "v3"

    async def get_tokens_by_user_id (self, user_id: str):

        try:
            logger.info("Fetching OAuth tokens for user_id: %s", user_id)
            tokens = await self.repository.get_tokens_by_user_id(user_id)

            if not tokens:
                logger.warning("OAuth tokens not found for user_id: %s", user_id)
                raise BadRequest(detail = "Conta Youtube não conectada")
            
            logger.info("OAuth tokens retrieved successfully for user_id: %s", user_id)
            return tokens[0], tokens[1]

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error fetching OAuth tokens for user_id %s: %s", user_id, str(e), exc_info=True)
            raise BadGateway
        
    async def create_user_oauth (self, user_id: str, code: str):

        try:
            logger.info("Starting OAuth connection flow for user_id: %s", user_id)
            response_dict = await self.get_tokens_by_authorization_code(code)

            logger.info("Authorization code exchanged successfully for user_id: %s", user_id)
            youtube_service = self.get_youtube_service(response_dict.get("access_token"), response_dict.get("refresh_token"))
            channel_id = await self.get_channel_id_by_current_user_oauth(youtube_service)
            logger.info("YouTube channel resolved successfully for user_id: %s, channel_id: %s", user_id, channel_id)

            date_expire_access, date_expire_refresh = self.calc_date_expire_tokens(response_dict.get("expires_in"),response_dict.get("refresh_token_expires_in"))

            response_dict["user_id"] = user_id
            response_dict["channel_id"] = channel_id
            response_dict["expires_in"] = date_expire_access
            response_dict["refresh_token_expires_in"] = date_expire_refresh

            result = await self.repository.create_user_oauth(response_dict)
            logger.info("OAuth connection stored successfully for user_id: %s", user_id)
            return result

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error creating OAuth connection for user_id %s: %s", user_id, str(e), exc_info=True)
            raise BadGateway
        
    async def get_tokens_by_authorization_code (self, code: str):

        try:
            logger.info("Exchanging authorization code for OAuth tokens")
            token_url = f"{TOKEN_URI}"
            data = {
                "code": code,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code"

            }
            async with httpx.AsyncClient() as client:
                response: httpx.Response = await client.post(url = token_url, data = data)

                if response.status_code == 400:
                    logger.warning("OAuth token exchange rejected with status 400")
                    raise BadRequest(detail = "Código de autorização inválido")
                
                response_dict = response.json()
                logger.info("OAuth token exchange completed successfully")
                return response_dict

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error exchanging authorization code for tokens: %s", str(e), exc_info=True)
            raise BadGateway

    async def get_channel_id_by_current_user_oauth (self, youtube_service):

        try:
            logger.info("Fetching current YouTube channel id")

            request = youtube_service.channels().list(part= "id", mine = True)

            response = await asyncio.to_thread(request.execute)

            items = response.get("items", [])

            if not items:
                logger.warning("No YouTube channel returned for the current OAuth user")
                raise NotFound(detail = "Não foi possível encontrar o canal")

            channel_id = items[0]["id"]

            logger.info("Current YouTube channel id fetched successfully: %s", channel_id)

            return channel_id
        
        except HttpError as error:
            status_code = error.resp.status

            if status_code == 404:
                logger.warning("YouTube channel not found while fetching current user channel id")
                raise NotFound(detail = "Não foi possível encontrar o canal")
            
            logger.error("YouTube API error fetching channel id (HTTP %s): %s", status_code, str(error), exc_info=True)
            raise BadRequest
            
        except Exception as e:
            logger.error("Unexpected error fetching current YouTube channel id: %s", str(e), exc_info=True)
            raise BadGateway

    def calc_date_expire_tokens (self, expires_in: int, refresh_token_expires_in: int):

        try:
            logger.info("Calculating OAuth token expiration dates")

            access_duration = timedelta(seconds = expires_in)
            refresh_duration = timedelta(seconds = refresh_token_expires_in)

            date_expire_access = datetime.now(timezone.utc) + access_duration
            date_expire_refresh = datetime.now(timezone.utc) + refresh_duration

            logger.info("OAuth token expiration dates calculated successfully")
            return date_expire_access, date_expire_refresh
        
        except Exception:
            logger.error("Unexpected error calculating OAuth token expiration dates", exc_info=True)
            raise

    def get_credencials_by_current_user_oauth (self, access_token: str, refresh_token: str):

        logger.info("Building credentials for current OAuth user")
        return Credentials(
            token = access_token,
            refresh_token = refresh_token, 
            token_uri = TOKEN_URI,
            client_id = CLIENT_ID,
            client_secret = CLIENT_SECRET
        )

    def get_youtube_service (self, access_token: str, refreh_token: str):

        logger.info("Building YouTube service client")
        credentials = self.get_credencials_by_current_user_oauth(access_token, refreh_token)

        logger.info("YouTube service client built successfully")
        return build(self.api_service_name, self.api_version, credentials = credentials)
