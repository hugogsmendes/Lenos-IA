from repository.oauth_repository import Oauth_Repository
from utils.exceptions import BadGateway, BadRequest, NotFound, Forbidden
from fastapi import HTTPException
from settings.config import Settings
import httpx
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
import asyncio

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

    async def get_oauth_by_user_id (self, user_id: str):

        try:
            oauth = await self.repository.get_oauth_by_user_id(user_id)

            if oauth:
                raise BadRequest(detail = "Conta Youtube já conectada")

            return None
        except HTTPException:
            raise
        except Exception as e:
            raise BadGateway
        
    async def create_oauth (self, user_id: str, code: str):

        try:
            response_dict = await self.get_tokens_by_oauth_code(code)

            credentials = self.get_credencials_by_current_user_oauth(response_dict.get("access_token"), response_dict.get("refresh_token"))
            channel_id = await self.get_channel_id_by_current_user_oauth(credentials)

            date_expire_access, date_expire_refresh = self.calc_date_expire_tokens(response_dict.get("expires_in"),response_dict.get("refresh_token_expires_in"))

            response_dict["user_id"] = user_id
            response_dict["channel_id"] = channel_id
            response_dict["expires_in"] = date_expire_access
            response_dict["refresh_token_expires_in"] = date_expire_refresh

            return await self.repository.create_oauth(response_dict)

        except HTTPException:
            raise
        except Exception as e:
            raise BadGateway
        
    async def get_tokens_by_oauth_code (self, code: str):

        try:
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
                    raise BadRequest(detail = "Código de autorização inválido")
                
                response_dict = response.json()
                return response_dict

        except HTTPException:
            raise
        except Exception as e:
            raise BadGateway

    async def get_channel_id_by_current_user_oauth (self, credentials: Credentials):

        try:
            youtube_service = build(self.api_service_name, self.api_version, credentials = credentials)

            request = youtube_service.channels().list(part= "id", mine = True)

            response = await asyncio.to_thread(request.execute)

            channel_id = response["items"][0]["id"]

            return channel_id
        
        except HttpError as error:
            status_code = error.resp.status

            if status_code == 404:
                raise NotFound(detail = "Não foi possível encontrar o canal")
            
        except Exception as e:
            raise BadGateway

    def calc_date_expire_tokens (self, expires_in: int, refresh_token_expires_in: int):

        try:

            access_duration = timedelta(seconds = expires_in)
            refresh_duration = timedelta(seconds = refresh_token_expires_in)

            date_expire_access = datetime.now(timezone.utc) + access_duration
            date_expire_refresh = datetime.now(timezone.utc) + refresh_duration

            return date_expire_access, date_expire_refresh
        
        except Exception as e:
            raise BadGateway

    def get_credencials_by_current_user_oauth (self, access_token: str, refresh_token: str):

        return Credentials(
            token = access_token,
            refresh_token = refresh_token, 
            token_uri = TOKEN_URI,
            client_id = CLIENT_ID,
            client_secret = CLIENT_SECRET
        )
        