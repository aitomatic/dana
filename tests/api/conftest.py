"""Pytest configuration for API tests."""

import os
import pytest
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dana.api.server.db import Base
from dana.api.server.models import Agent

# Set test database URL
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Set up test database environment for the entire test session."""
    # Set environment variable for test database
    os.environ["DANA_DATABASE_URL"] = TEST_DATABASE_URL
    
    # Create test engine
    test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    yield test_engine, TestSessionLocal
    
    # Clean up after all tests
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    
    # Remove test database file
    if os.path.exists("./test.db"):
        os.remove("./test.db")
    
    # Restore original environment
    if "DANA_DATABASE_URL" in os.environ:
        del os.environ["DANA_DATABASE_URL"]


@pytest.fixture(scope="function")
def db_session(setup_test_database):
    """Create a test database session with tables created."""
    test_engine, TestSessionLocal = setup_test_database
    
    # Create session
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_agent(db_session: Session):
    """Create a sample agent for testing."""
    agent = Agent(name="Sample Agent", description="A sample agent for testing", config={"model": "gpt-4", "temperature": 0.7})
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    return agent
