"""
database.py
-------------
Handles the PostgreSQL connection using SQLAlchemy.

- Reads the connection string from the DATABASE_URL environment variable
  (falls back to a local default so the project runs out-of-the-box).
- Exposes `Base` for models to inherit from.
- Exposes `get_db()` as a FastAPI dependency that yields a DB session
  and always closes it afterwards.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load variables from a .env file if present (see .env.example)
load_dotenv()

# Example: postgresql://postgres:password@localhost:5432/company_brain
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/company_brain",
)

# `pool_pre_ping` avoids "server closed the connection unexpectedly" errors
# on long-lived connections (common with free-tier / cloud Postgres).
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a SQLAlchemy session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
