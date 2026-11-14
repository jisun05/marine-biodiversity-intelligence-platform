import os
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session, sessionmaker


# Load environment variables from the project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")


# Read database configuration
POSTGRES_DB = os.getenv("POSTGRES_DB")
TEST_POSTGRES_DB = os.getenv("TEST_POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

if not all([POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD]):
    raise RuntimeError("Database environment variables are missing.")


# Create database URL
def build_database_url(database_name: str) -> URL:
    return URL.create(
        drivername="postgresql+psycopg",
        username=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host="localhost",
        port=5432,
        database=database_name,
    )


# Development database
DATABASE_URL = build_database_url(POSTGRES_DB)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# Test database
test_engine = None
TestSessionLocal = None

if TEST_POSTGRES_DB:
    TEST_DATABASE_URL = build_database_url(TEST_POSTGRES_DB)

    test_engine = create_engine(
        TEST_DATABASE_URL,
        pool_pre_ping=True,
    )

    TestSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
    )


# FastAPI database dependency
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()