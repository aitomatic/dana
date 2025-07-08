"""Pytest configuration for API tests."""

import pytest
from sqlalchemy.orm import Session
from dana.api.server.db import Base, engine, SessionLocal
from dana.api.server.models import Agent


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session with tables created."""
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_agent(db_session: Session):
    """Create a sample agent for testing."""
    agent = Agent(name="Sample Agent", description="A sample agent for testing", config={"model": "gpt-4", "temperature": 0.7})
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    return agent
