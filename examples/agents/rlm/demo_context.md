

## [file: sample_context.md] 2026-01-13T12:05:52.485070

# Sample Codebase Documentation

This is a sample large document for demonstrating the RLM (Recursive Language Model) pattern.

## Authentication Module

### auth/login.py

```python
def authenticate_user(username: str, password: str) -> bool:
    """
    Authenticate a user with username and password.

    Args:
        username: The user's username
        password: The user's password (will be hashed)

    Returns:
        True if authentication successful, False otherwise
    """
    user = get_user_by_username(username)
    if not user:
        return False
    return verify_password(password, user.password_hash)


def create_session(user_id: int) -> str:
    """Create a new session token for the authenticated user."""
    token = generate_secure_token()
    store_session(user_id, token)
    return token
```

### auth/oauth.py

```python
def oauth_callback(provider: str, code: str) -> User:
    """
    Handle OAuth callback from external providers.

    Supports: Google, GitHub, Microsoft
    """
    token = exchange_code_for_token(provider, code)
    user_info = get_user_info(provider, token)
    return find_or_create_user(user_info)
```

## Error Handling Patterns

### errors/handlers.py

```python
class AppError(Exception):
    """Base application error."""
    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
        super().__init__(message)


class ValidationError(AppError):
    """Raised when input validation fails."""
    def __init__(self, field: str, message: str):
        super().__init__(f"Validation failed for {field}: {message}", code=400)
        self.field = field


class NotFoundError(AppError):
    """Raised when a resource is not found."""
    def __init__(self, resource: str, id: str):
        super().__init__(f"{resource} with id {id} not found", code=404)


def handle_error(error: Exception) -> dict:
    """Convert exception to API response format."""
    if isinstance(error, AppError):
        return {"error": error.message, "code": error.code}
    # Log unexpected errors
    log_error(error)
    return {"error": "Internal server error", "code": 500}
```

### errors/middleware.py

```python
async def error_middleware(request, call_next):
    """Middleware to catch and handle all errors."""
    try:
        response = await call_next(request)
        return response
    except AppError as e:
        return JSONResponse(
            status_code=e.code,
            content=handle_error(e)
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content=handle_error(e)
        )
```

## Database Models

### models/user.py

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    sessions = relationship("Session", back_populates="user")

    def verify_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
```

### models/session.py

```python
class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="sessions")

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
```

## API Endpoints

### api/auth_routes.py

```python
@router.post("/login")
async def login(credentials: LoginRequest) -> TokenResponse:
    """
    Authenticate user and return session token.

    Errors:
        401: Invalid credentials
        429: Too many login attempts
    """
    if not authenticate_user(credentials.username, credentials.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_session(user.id)
    return TokenResponse(token=token, expires_in=3600)


@router.post("/logout")
async def logout(token: str = Depends(get_current_token)):
    """Invalidate the current session token."""
    invalidate_session(token)
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user(user: User = Depends(get_authenticated_user)):
    """Get the currently authenticated user's profile."""
    return UserResponse.from_orm(user)
```

## Configuration

### config/settings.py

```python
class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # Database
    DATABASE_URL: str = "postgresql://localhost/app"

    # Security
    SECRET_KEY: str
    TOKEN_EXPIRY_SECONDS: int = 3600

    # OAuth providers
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
```

## Utility Functions

### utils/security.py

```python
def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hash: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode(), hash.encode())
```

### utils/logging.py

```python
def setup_logging():
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def log_error(error: Exception, context: dict = None):
    """Log an error with optional context."""
    logger.error(
        f"Error: {type(error).__name__}: {error}",
        extra={"context": context or {}}
    )
```

---

This document contains approximately 5,000 characters representing a typical small codebase.
In practice, the RLM pattern is designed for documents 10-100x larger (500K+ tokens).


## [file: sample_context.md] 2026-01-13T12:06:11.576156

# Sample Codebase Documentation

This is a sample large document for demonstrating the RLM (Recursive Language Model) pattern.

## Authentication Module

### auth/login.py

```python
def authenticate_user(username: str, password: str) -> bool:
    """
    Authenticate a user with username and password.

    Args:
        username: The user's username
        password: The user's password (will be hashed)

    Returns:
        True if authentication successful, False otherwise
    """
    user = get_user_by_username(username)
    if not user:
        return False
    return verify_password(password, user.password_hash)


def create_session(user_id: int) -> str:
    """Create a new session token for the authenticated user."""
    token = generate_secure_token()
    store_session(user_id, token)
    return token
```

### auth/oauth.py

```python
def oauth_callback(provider: str, code: str) -> User:
    """
    Handle OAuth callback from external providers.

    Supports: Google, GitHub, Microsoft
    """
    token = exchange_code_for_token(provider, code)
    user_info = get_user_info(provider, token)
    return find_or_create_user(user_info)
```

## Error Handling Patterns

### errors/handlers.py

```python
class AppError(Exception):
    """Base application error."""
    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
        super().__init__(message)


class ValidationError(AppError):
    """Raised when input validation fails."""
    def __init__(self, field: str, message: str):
        super().__init__(f"Validation failed for {field}: {message}", code=400)
        self.field = field


class NotFoundError(AppError):
    """Raised when a resource is not found."""
    def __init__(self, resource: str, id: str):
        super().__init__(f"{resource} with id {id} not found", code=404)


def handle_error(error: Exception) -> dict:
    """Convert exception to API response format."""
    if isinstance(error, AppError):
        return {"error": error.message, "code": error.code}
    # Log unexpected errors
    log_error(error)
    return {"error": "Internal server error", "code": 500}
```

### errors/middleware.py

```python
async def error_middleware(request, call_next):
    """Middleware to catch and handle all errors."""
    try:
        response = await call_next(request)
        return response
    except AppError as e:
        return JSONResponse(
            status_code=e.code,
            content=handle_error(e)
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content=handle_error(e)
        )
```

## Database Models

### models/user.py

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    sessions = relationship("Session", back_populates="user")

    def verify_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
```

### models/session.py

```python
class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="sessions")

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
```

## API Endpoints

### api/auth_routes.py

```python
@router.post("/login")
async def login(credentials: LoginRequest) -> TokenResponse:
    """
    Authenticate user and return session token.

    Errors:
        401: Invalid credentials
        429: Too many login attempts
    """
    if not authenticate_user(credentials.username, credentials.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_session(user.id)
    return TokenResponse(token=token, expires_in=3600)


@router.post("/logout")
async def logout(token: str = Depends(get_current_token)):
    """Invalidate the current session token."""
    invalidate_session(token)
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user(user: User = Depends(get_authenticated_user)):
    """Get the currently authenticated user's profile."""
    return UserResponse.from_orm(user)
```

## Configuration

### config/settings.py

```python
class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # Database
    DATABASE_URL: str = "postgresql://localhost/app"

    # Security
    SECRET_KEY: str
    TOKEN_EXPIRY_SECONDS: int = 3600

    # OAuth providers
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
```

## Utility Functions

### utils/security.py

```python
def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hash: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode(), hash.encode())
```

### utils/logging.py

```python
def setup_logging():
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def log_error(error: Exception, context: dict = None):
    """Log an error with optional context."""
    logger.error(
        f"Error: {type(error).__name__}: {error}",
        extra={"context": context or {}}
    )
```

---

This document contains approximately 5,000 characters representing a typical small codebase.
In practice, the RLM pattern is designed for documents 10-100x larger (500K+ tokens).
