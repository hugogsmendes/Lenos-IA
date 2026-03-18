from dotenv import load_dotenv
import os 
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
import asyncio

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
                    
engine = create_async_engine(DATABASE_URL,
                             pool_pre_ping = True,
                             echo = True, # False em produção
                             pool_size = 20,
                             max_overflow = 10)

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
            
    assert asyncio.run(test_connect()) == "Connection successful!"

