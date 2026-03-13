import os

from sqlalchemy import create_engine, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

# =======================================================
# DATABASE URL
# Reads from environment variable.
# For Google Cloud Run + Cloud SQL use:
#   postgresql+psycopg2://USER:PASSWORD@/DBNAME?host=/cloudsql/PROJECT:REGION:INSTANCE
# For local development use:
#   postgresql+psycopg2://USER:PASSWORD@localhost:5432/DBNAME
#   or sqlite:///./credit_engine.db
# =======================================================

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./credit_engine.db")

# Heroku/Cloud providers sometimes prefix with "postgres://" – fix it for SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

_is_postgres = DATABASE_URL.startswith("postgresql")

# =======================================================
# JSON COLUMN TYPE
# Export JSONType so models can use JSONB on PostgreSQL
# and fall back to plain JSON on SQLite.
# =======================================================

if _is_postgres:
    from sqlalchemy.dialects.postgresql import JSONB as JSONType
else:
    JSONType = JSON

# =======================================================
# ENGINE
# =======================================================

if _is_postgres:
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
