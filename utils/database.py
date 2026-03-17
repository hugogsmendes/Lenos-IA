from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
import os 
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
                    
engine = create_engine(DATABASE_URL, pool_pre_ping = True)

Base = declarative_base() 

SessionLocal = sessionmaker(bind = engine) 

if __name__ == "__main__":

    def test_connect():

        try:
            with engine.connect() as connection:
                return "Connection successful!"
        except Exception as e:
            print(f"Failed to connect: {e}")
            
    assert test_connect() == "Connection successful!"

