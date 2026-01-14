# Sample Codebase

This is a simulated large codebase for demonstrating RLM-based querying.
In a real scenario, this would be 500K+ tokens of actual code.

## src/auth/handlers.py

```python
"""Authentication handlers for the application."""

from datetime import datetime, timedelta
from typing import Optional
import hashlib
import secrets

from .models import User, Session
from .tokens import create_jwt, verify_jwt


def login(username: str, password: str) -> Optional[Session]:
    """
    Authenticate a user and create a session.

    Args:
        username: The user's username
        password: The user's password

    Returns:
        Session object if successful, None otherwise
    """
    user = User.get_by_username(username)
    if not user:
        return None

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if user.password_hash != password_hash:
        return None

    session = Session.create(
        user_id=user.id,
        token=secrets.token_urlsafe(32),
        expires_at=datetime.now() + timedelta(hours=24)
    )
    return session


def verify_token(token: str) -> Optional[User]:
    """
    Verify an authentication token and return the associated user.

    Args:
        token: JWT or session token to verify

    Returns:
        User object if token is valid, None otherwise
    """
    # Try JWT first
    payload = verify_jwt(token)
    if payload:
        return User.get_by_id(payload['user_id'])

    # Fall back to session token
    session = Session.get_by_token(token)
    if session and session.expires_at > datetime.now():
        return User.get_by_id(session.user_id)

    return None


def refresh_session(session: Session) -> Session:
    """
    Refresh a session, extending its expiration time.

    Args:
        session: The session to refresh

    Returns:
        Updated session with new expiration
    """
    session.expires_at = datetime.now() + timedelta(hours=24)
    session.save()
    return session


def logout(session: Session) -> bool:
    """
    Log out a user by invalidating their session.

    Args:
        session: The session to invalidate

    Returns:
        True if successful
    """
    session.delete()
    return True
```

## src/auth/tokens.py

```python
"""JWT token handling utilities."""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"


def create_jwt(user_id: int, expires_in: int = 3600) -> str:
    """
    Create a JWT token for a user.

    Args:
        user_id: The user's ID to encode
        expires_in: Expiration time in seconds

    Returns:
        Encoded JWT string
    """
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(seconds=expires_in),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.

    Args:
        token: The JWT to verify

    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
```

## src/auth/models.py

```python
"""Data models for authentication."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    id: int
    username: str
    email: str
    password_hash: str
    created_at: datetime

    @classmethod
    def get_by_id(cls, user_id: int) -> Optional['User']:
        """Retrieve a user by ID from the database."""
        # Database query implementation
        pass

    @classmethod
    def get_by_username(cls, username: str) -> Optional['User']:
        """Retrieve a user by username from the database."""
        # Database query implementation
        pass


@dataclass
class Session:
    id: int
    user_id: int
    token: str
    expires_at: datetime
    created_at: datetime

    @classmethod
    def create(cls, user_id: int, token: str, expires_at: datetime) -> 'Session':
        """Create a new session in the database."""
        # Database insert implementation
        pass

    @classmethod
    def get_by_token(cls, token: str) -> Optional['Session']:
        """Retrieve a session by its token."""
        # Database query implementation
        pass

    def save(self) -> None:
        """Save session changes to database."""
        # Database update implementation
        pass

    def delete(self) -> None:
        """Delete this session from the database."""
        # Database delete implementation
        pass
```

## src/api/routes.py

```python
"""API route definitions."""

from flask import Flask, request, jsonify
from functools import wraps

from auth.handlers import login, verify_token, logout


app = Flask(__name__)


def require_auth(f):
    """Decorator to require authentication for a route."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        user = verify_token(token)
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
        request.user = user
        return f(*args, **kwargs)
    return decorated


@app.route('/api/login', methods=['POST'])
def api_login():
    """Handle login requests."""
    data = request.json
    session = login(data['username'], data['password'])
    if session:
        return jsonify({'token': session.token})
    return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/api/logout', methods=['POST'])
@require_auth
def api_logout():
    """Handle logout requests."""
    logout(request.session)
    return jsonify({'success': True})


@app.route('/api/profile', methods=['GET'])
@require_auth
def api_profile():
    """Get current user profile."""
    return jsonify({
        'id': request.user.id,
        'username': request.user.username,
        'email': request.user.email
    })
```

## src/utils/helpers.py

```python
"""General utility functions."""

import re
from typing import List


def validate_email(email: str) -> bool:
    """Validate an email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> List[str]:
    """
    Validate password strength.

    Returns list of validation errors, empty if valid.
    """
    errors = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters")
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain uppercase letter")
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain lowercase letter")
    if not re.search(r'\d', password):
        errors.append("Password must contain a digit")
    return errors


def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS."""
    replacements = {
        '<': '&lt;',
        '>': '&gt;',
        '&': '&amp;',
        '"': '&quot;',
        "'": '&#x27;'
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text
```

## src/database/connection.py

```python
"""Database connection management."""

import sqlite3
from contextlib import contextmanager
from typing import Generator


DATABASE_PATH = "app.db"


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """Get a database connection with automatic cleanup."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Initialize database tables."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
```

## tests/test_auth.py

```python
"""Tests for authentication functionality."""

import pytest
from datetime import datetime, timedelta

from auth.handlers import login, verify_token, refresh_session
from auth.tokens import create_jwt, verify_jwt


class TestLogin:
    def test_successful_login(self, mock_user):
        session = login("testuser", "correctpassword")
        assert session is not None
        assert session.user_id == mock_user.id

    def test_wrong_password(self, mock_user):
        session = login("testuser", "wrongpassword")
        assert session is None

    def test_nonexistent_user(self):
        session = login("nobody", "password")
        assert session is None


class TestVerifyToken:
    def test_valid_jwt(self, mock_user):
        token = create_jwt(mock_user.id)
        user = verify_token(token)
        assert user is not None
        assert user.id == mock_user.id

    def test_expired_jwt(self, mock_user):
        token = create_jwt(mock_user.id, expires_in=-100)
        user = verify_token(token)
        assert user is None

    def test_valid_session_token(self, mock_session):
        user = verify_token(mock_session.token)
        assert user is not None


class TestRefreshSession:
    def test_refresh_extends_expiration(self, mock_session):
        old_expiry = mock_session.expires_at
        refreshed = refresh_session(mock_session)
        assert refreshed.expires_at > old_expiry
```
