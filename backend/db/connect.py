import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# In docker-compose we will set DATABASE_URL directly
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # fallback for local dev
    DB_USER = os.getenv("DB_USER", "por")
    DB_PASS = os.getenv("DB_PASS", "por")
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")  # local DB
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "por")
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
