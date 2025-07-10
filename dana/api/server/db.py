import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Use environment variable for database URL, default to local.db for development
SQLALCHEMY_DATABASE_URL = os.environ.get("DANA_DATABASE_URL", "sqlite:///./local.db")

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Add get_db for dependency injection and testing

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
