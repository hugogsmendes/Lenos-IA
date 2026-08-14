from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings (BaseSettings):
	model_config = SettingsConfigDict(env_file = ".env", env_file_encoding = "utf-8")

	YOUTUBE_API_KEY: str
	GEMINI_API_KEY: str
	PEPPER: str
	ALEMBIC_URL: str | None = None
	DATABASE_URL_SESSION: str | None = None
	DATABASE_URL_TRANSACTION: str
	SECRET_KEY: str
	ALGORITHM: str
	ACCESS_TOKEN_EXPIRE: int
	REFRESH_TOKEN_EXPIRE: int
	ENV: str
	RESEND_API_KEY: str
	EMAIL_FROM: str
	FRONT: str
	REDIS_URL: str
	SCOPE: str
	CLIENT_ID: str
	REDIRECT_URI: str
	AUTH_URI: str
	CLIENT_SECRET: str
	TOKEN_URI: str
	