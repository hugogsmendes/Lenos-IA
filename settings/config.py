from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings (BaseSettings):
	model_config = SettingsConfigDict(env_file = ".env", env_file_encoding = "utf-8")

	key_youtube: str
	key_gemini: str
	pepper: str
	ALEMBIC_URL: str | None = None
	DATABASE_URL_SESSION: str | None = None
	DATABASE_URL_TRANSACTION: str
	SECRET_KEY: str
	ALGORITHM: str
	ACCESS_TOKEN_EXPIRE: int
	REFRESH_TOKEN_EXPIRE: int
	ENV: str
	key_resend: str
	email_from: str
	front: str
	REDIS_URL: str
	