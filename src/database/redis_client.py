from src.settings.config import settings
from redis.asyncio import Redis, ConnectionPool


REDIS_URL = settings.REDIS_URL

pool = ConnectionPool.from_url(
    url = REDIS_URL,
    max_connections = 10,
    decode_responses = True,
)

async def get_redis() -> Redis:
    return Redis(connection_pool = pool)

