from redis.asyncio import Redis, ConnectionPool
from dotenv import load_dotenv
import os

load_dotenv()

URL = os.getenv("REDIS_URL")

pool = ConnectionPool.from_url(
    url = URL,
    max_connections = 10,
    decode_responses = True,
)

async def get_redis() -> Redis:
    return Redis(connection_pool = pool)

