"""Pytest configuration for API tests."""

import os
import tempfile
import uuid
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def _make_temp_db_url():
    temp_db = tempfile.NamedTemporaryFile(suffix=f"_{uuid.uuid4().hex[:8]}.db", delete=False)
    return temp_db, f"sqlite:///{temp_db.name}"

@pytest.fixture(scope="function")
def test_db():
    """Create a temp SQLite DB, engine, and session factory for each test. Clean up after."""
    temp_db, test_database_url = _make_temp_db_url()
    os.environ["DANA_DATABASE_URL"] = test_database_url
    from dana.api.core.models import Base
    engine = create_engine(test_database_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield engine, SessionLocal, temp_db
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    temp_db.close()
    os.unlink(temp_db.name)

@pytest.fixture(scope="function")
def db_session(test_db):
    """Yield a session using the test DB. Clear all tables before each test."""
    _, SessionLocal, _ = test_db
    session = SessionLocal()
    from dana.api.core.models import Agent, Topic, Document, Conversation, Message
    # Clear all tables in reverse dependency order
    session.query(Message).delete()
    session.query(Document).delete()
    session.query(Conversation).delete()
    session.query(Topic).delete()
    session.query(Agent).delete()
    session.commit()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture(scope="function")
def client(test_db):
    """Yield a TestClient using the test DB."""
    engine, SessionLocal, _ = test_db
    from unittest.mock import patch

    from dana.api.core.database import get_db
    from dana.api.server.server import create_app
    app = create_app()
    # Remove all startup event handlers to prevent demo data insertion
    app.router.on_startup.clear()
    def override_get_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()
    app.dependency_overrides[get_db] = override_get_db
    with patch('dana.api.core.database.engine', engine), \
         patch('dana.api.core.database.SessionLocal', SessionLocal):
        with TestClient(app) as test_client:
            yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def mock_db():
    """Create a mock database session for testing."""
    return Mock(spec=Session)

@pytest.fixture
def sample_agent():
    """Create a sample agent for testing without database."""
    from dana.api.core.models import Agent
    return Agent(
        id=1,
        name="Sample Agent", 
        description="A sample agent for testing", 
        config={"model": "gpt-4", "temperature": 0.7}
    )

@pytest.fixture
def sample_conversation():
    """Create a sample conversation for testing without database."""
    from dana.api.core.models import Conversation
    return Conversation(
        id=1,
        title="Test Conversation",
        created_at="2025-01-27T10:00:00",
        updated_at="2025-01-27T10:00:00"
    )

@pytest.fixture
def sample_message():
    """Create a sample message for testing without database."""
    from dana.api.core.models import Message
    return Message(
        id=1,
        conversation_id=1,
        sender="user",
        content="Hello, agent!",
        created_at="2025-01-27T10:00:00",
        updated_at="2025-01-27T10:00:00"
    )

@pytest.fixture
def mock_get_db(mock_db):
    """Mock the get_db dependency."""
    def _get_db():
        yield mock_db
    return _get_db

@pytest.fixture
def mock_chat_service():
    """Mock the chat service dependency."""
    from dana.api.services.chat_service import ChatService
    chat_service = Mock(spec=ChatService)
    return chat_service
