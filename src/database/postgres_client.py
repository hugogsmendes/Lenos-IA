from src.settings.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool


DATABASE_URL_TRANSACTION = settings.DATABASE_URL_TRANSACTION
                    
engine = create_async_engine(DATABASE_URL_TRANSACTION,
                             pool_pre_ping = True,
                             poolclass = NullPool,
                             echo = False, # False em produção
                             connect_args = {"statement_cache_size": 0}) 


Base = declarative_base() 

SessionLocal = async_sessionmaker(bind = engine, 
                                  class_ = AsyncSession,
                                  expire_on_commit = False,
                                  autocommit = False,
                                  autoflush = False) 

if __name__ == "__main__":

    async def test_connect():

        try:
            async with engine.connect() as conn:
                return "Connection successful!"
        except Exception as e:
            print(f"Failed to connect: {e}")
        finally:
            await engine.dispose()