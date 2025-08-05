import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Use environment variable for database URL, default to local.db for development
SQLALCHEMY_DATABASE_URL = os.environ.get("DANA_DATABASE_URL", "sqlite:///./local.db")

# Create engine with proper configuration for SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,  # Set echo to boolean
    pool_size=10,  # Add pool_size for SQLite
    max_overflow=20,  # Add max_overflow for SQLite
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Add get_db for dependency injection and testing
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
