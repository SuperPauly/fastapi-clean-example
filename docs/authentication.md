# 🔐 Authentication System Documentation

This document provides comprehensive documentation for the authentication system in the FastAPI Clean Architecture Template.

## Overview

The authentication system follows hexagonal architecture principles and provides:

- **Traditional Authentication** (email/password with JWT tokens)
- **Social Authentication** (13+ OAuth providers)
- **Role-Based Access Control (RBAC)** with hierarchical permissions
- **Email Verification** and password reset functionality
- **Account Security** with lockout protection and breach detection
- **Rate Limiting** integration
- **Security Logging** and monitoring

## Architecture

The authentication system is organized across the hexagonal architecture layers:

### Domain Layer (`src/domain/`)
- **Entities**: `User` - Rich domain entity with business logic
- **Value Objects**: `Email`, `Password`, `UserRole`, `AuthToken`
- **Domain Services**: `AuthenticationDomainService` - Core business logic

### Application Layer (`src/application/`)
- **Use Cases**: `RegisterUser`, `AuthenticateUser`, `SocialLogin`
- **Ports**: `UserRepository`, `AuthenticationService`, `TokenService`
- **Services**: Application-specific orchestration logic

### Infrastructure Layer (`src/infrastructure/`)
- **Database Models**: Tortoise ORM models for persistence
- **Repositories**: Database adapters implementing ports
- **Services**: JWT, OAuth, email, and external service adapters

### Presentation Layer (`src/presentation/`)
- **API Endpoints**: FastAPI routers for authentication
- **Middleware**: Authentication and rate limiting middleware
- **Schemas**: Request/response models

## Configuration

### Basic Setup

The authentication system is configured via Dynaconf settings:

```toml
[authentication]
enable_registration = true
enable_email_verification = true
enable_password_reset = true
enable_social_login = true
enable_rbac = true
default_user_role = "user"

# Email verification settings
email_verification_expire_hours = 24
email_verification_required = true
resend_verification_cooldown_minutes = 5

# Password reset settings
password_reset_expire_hours = 2
password_reset_cooldown_minutes = 15

# Account lockout settings
max_login_attempts = 5
lockout_duration_minutes = 30
enable_account_lockout = true

# Available roles and hierarchy
available_roles = ["user", "moderator", "admin", "superuser"]
role_hierarchy = {
    "user" = 1,
    "moderator" = 2,
    "admin" = 3,
    "superuser" = 4
}

[security]
# JWT settings
jwt_secret_key = "your-jwt-secret-key-change-this-in-production"
jwt_algorithm = "HS256"
jwt_expire_minutes = 30
jwt_refresh_expire_days = 7

# Session settings
session_secret_key = "your-session-secret-key-change-this-in-production"
session_expire_minutes = 60
session_cookie_secure = true
session_cookie_httponly = true

# Password policy
password_min_length = 8
password_require_uppercase = true
password_require_lowercase = true
password_require_numbers = true
password_require_special = true
```

### OAuth Configuration

Configure OAuth providers in the `[oauth]` section:

```toml
[oauth]
redirect_url = "http://localhost:8000/auth/callback"
state_secret = "your-oauth-state-secret-change-this"

# Google OAuth
google_enabled = true
google_client_id = "your-google-client-id"
google_client_secret = "your-google-client-secret"
google_scopes = ["openid", "email", "profile"]

# GitHub OAuth
github_enabled = true
github_client_id = "your-github-client-id"
github_client_secret = "your-github-client-secret"
github_scopes = ["user:email"]

# Add similar configuration for other providers...
```

### Interactive Configuration

Use the authentication setup TUI for interactive configuration:

```bash
# Launch interactive configuration tool
python auth_setup_tui.py

# Configure specific provider
python auth_setup_tui.py --provider google --interactive

# Generate new secret keys
python auth_setup_tui.py --generate-secrets
```

## Usage Examples

### 1. User Registration

```python
from src.application.use_cases.register_user import RegisterUserUseCase, RegisterUserRequest

# Initialize use case with dependencies
register_use_case = RegisterUserUseCase(
    user_repository=user_repository,
    auth_service=auth_service,
    token_service=token_service,
    require_email_verification=True
)

# Register new user
request = RegisterUserRequest(
    email="user@example.com",
    password="SecurePassword123!",
    username="newuser",
    first_name="John",
    last_name="Doe",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0..."
)

response = await register_use_case.execute(request)

if response.success:
    print(f"User registered with ID: {response.user_id}")
    if response.requires_verification:
        print("Verification email sent")
else:
    print(f"Registration failed: {response.error_message}")
```

### 2. User Authentication

```python
from src.application.use_cases.authenticate_user import AuthenticateUserUseCase, AuthenticateUserRequest

# Initialize use case
auth_use_case = AuthenticateUserUseCase(
    user_repository=user_repository,
    auth_service=auth_service,
    token_service=token_service
)

# Authenticate user
request = AuthenticateUserRequest(
    email="user@example.com",
    password="SecurePassword123!",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0...",
    remember_me=True
)

response = await auth_use_case.execute(request)

if response.success:
    print(f"Authentication successful!")
    print(f"Access Token: {response.access_token}")
    print(f"Refresh Token: {response.refresh_token}")
    print(f"User Info: {response.user_info}")
else:
    print(f"Authentication failed: {response.error_message}")
    if response.account_locked:
        print(f"Account locked until: {response.lockout_expires_at}")
```

### 3. Social Authentication

```python
from src.application.use_cases.social_login import SocialLoginUseCase, SocialLoginRequest

# Initialize use case
social_use_case = SocialLoginUseCase(
    user_repository=user_repository,
    auth_service=auth_service,
    token_service=token_service,
    auto_create_users=True
)

# Get authorization URL
auth_url_result = await social_use_case.get_authorization_url(
    provider="google",
    redirect_uri="http://localhost:8000/auth/callback",
    scopes=["openid", "email", "profile"]
)

print(f"Redirect user to: {auth_url_result['authorization_url']}")

# After user returns with authorization code
request = SocialLoginRequest(
    provider="google",
    authorization_code="auth_code_from_callback",
    redirect_uri="http://localhost:8000/auth/callback",
    state="state_from_callback",
    ip_address="192.168.1.1"
)

response = await social_use_case.execute(request)

if response.success:
    print(f"Social login successful!")
    print(f"New user: {response.is_new_user}")
    print(f"Access Token: {response.access_token}")
else:
    print(f"Social login failed: {response.error_message}")
```

### 4. FastAPI Integration with Rate Limiting

```python
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer
from src.infrastructure.rate_limiting.decorators import rate_limit
from src.presentation.api.dependencies.auth_dependencies import get_current_user

app = FastAPI()
security = HTTPBearer()

@app.post("/auth/register")
@rate_limit(key="register", limit=5, window=3600)  # 5 registrations per hour
async def register_user(
    request: Request,
    user_data: RegisterUserSchema,
    register_use_case: RegisterUserUseCase = Depends()
):
    """Register a new user with rate limiting."""
    register_request = RegisterUserRequest(
        email=user_data.email,
        password=user_data.password,
        username=user_data.username,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    response = await register_use_case.execute(register_request)
    
    if not response.success:
        raise HTTPException(status_code=400, detail=response.error_message)
    
    return {
        "message": "Registration successful",
        "user_id": response.user_id,
        "requires_verification": response.requires_verification
    }

@app.post("/auth/login")
@rate_limit(key="login", limit=10, window=900)  # 10 login attempts per 15 minutes
async def login_user(
    request: Request,
    credentials: LoginSchema,
    auth_use_case: AuthenticateUserUseCase = Depends()
):
    """Authenticate user with rate limiting."""
    auth_request = AuthenticateUserRequest(
        email=credentials.email,
        password=credentials.password,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        remember_me=credentials.remember_me
    )
    
    response = await auth_use_case.execute(auth_request)
    
    if not response.success:
        raise HTTPException(status_code=401, detail=response.error_message)
    
    return {
        "access_token": response.access_token,
        "refresh_token": response.refresh_token,
        "token_type": response.token_type,
        "expires_in": response.expires_in,
        "user": response.user_info
    }

@app.get("/auth/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile (requires authentication)."""
    return {
        "id": current_user.id,
        "email": current_user.email.value,
        "username": current_user.username,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": current_user.role.value,
        "permissions": current_user.permissions,
        "is_verified": current_user.is_verified,
        "last_login_at": current_user.last_login_at
    }

@app.get("/admin/users")
async def list_users(
    current_user: User = Depends(get_current_user),
    user_repository: UserRepositoryPort = Depends()
):
    """List users (requires admin role)."""
    # Check if user has admin role
    if not current_user.can_access_resource("admin", ["user:read_others_profile"]):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    users = await user_repository.list_users(limit=50)
    return [user.to_dict() for user in users]
```

### 5. Database Integration with Tortoise ORM

```python
from tortoise.models import Model
from tortoise import fields
from src.domain.entities.user import User as UserEntity
from src.domain.value_objects.email import Email
from src.domain.value_objects.user_role import UserRole

class UserModel(Model):
    """Tortoise ORM model for User entity."""
    
    id = fields.IntField(pk=True)
    email = fields.CharField(max_length=254, unique=True, index=True)
    username = fields.CharField(max_length=50, unique=True, null=True, index=True)
    password_hash = fields.TextField(null=True)
    
    # Profile fields
    first_name = fields.CharField(max_length=50, null=True)
    last_name = fields.CharField(max_length=50, null=True)
    display_name = fields.CharField(max_length=100, null=True)
    avatar_url = fields.TextField(null=True)
    bio = fields.TextField(null=True)
    
    # Authentication fields
    is_verified = fields.BooleanField(default=False)
    is_active = fields.BooleanField(default=True)
    status = fields.CharField(max_length=20, default="pending_verification")
    role = fields.CharField(max_length=20, default="user")
    permissions = fields.JSONField(default=list)
    
    # Security fields
    failed_login_attempts = fields.IntField(default=0)
    last_login_at = fields.DatetimeField(null=True)
    last_login_ip = fields.CharField(max_length=45, null=True)
    locked_until = fields.DatetimeField(null=True)
    
    # Social accounts
    social_accounts = fields.JSONField(default=list)
    
    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "users"
        indexes = [
            ("email",),
            ("username",),
            ("status",),
            ("role",),
            ("created_at",),
        ]
    
    def to_domain_entity(self) -> UserEntity:
        """Convert ORM model to domain entity."""
        from src.domain.value_objects.password import Password
        
        return UserEntity(
            id=self.id,
            email=Email(self.email),
            password=Password.create_from_hash(self.password_hash) if self.password_hash else None,
            username=self.username,
            first_name=self.first_name,
            last_name=self.last_name,
            display_name=self.display_name,
            avatar_url=self.avatar_url,
            bio=self.bio,
            role=UserRole(self.role),
            permissions=self.permissions,
            is_verified=self.is_verified,
            is_active=self.is_active,
            status=UserStatus(self.status),
            failed_login_attempts=self.failed_login_attempts,
            last_login_at=self.last_login_at,
            last_login_ip=self.last_login_ip,
            locked_until=self.locked_until,
            social_accounts=self.social_accounts,
            created_at=self.created_at,
            updated_at=self.updated_at
        )

class AuthTokenModel(Model):
    """Tortoise ORM model for authentication tokens."""
    
    id = fields.IntField(pk=True)
    token_hash = fields.CharField(max_length=64, unique=True, index=True)
    token_type = fields.CharField(max_length=20, index=True)
    user = fields.ForeignKeyField("models.UserModel", related_name="tokens")
    
    expires_at = fields.DatetimeField(null=True, index=True)
    is_revoked = fields.BooleanField(default=False, index=True)
    used_at = fields.DatetimeField(null=True)
    metadata = fields.JSONField(default=dict)
    
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "auth_tokens"
        indexes = [
            ("token_hash",),
            ("token_type", "user_id"),
            ("expires_at",),
            ("is_revoked",),
        ]
```

### 6. Custom Middleware Integration

```python
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from src.infrastructure.rate_limiting.pyrate_adapter import RateLimiter

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for authentication and rate limiting."""
    
    def __init__(self, app, rate_limiter: RateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter
    
    async def dispatch(self, request: Request, call_next):
        # Apply rate limiting to authentication endpoints
        if request.url.path.startswith("/auth/"):
            client_ip = request.client.host
            
            # Check rate limit
            is_allowed = await self.rate_limiter.check_rate_limit(
                key=f"auth:{client_ip}",
                limit=20,  # 20 requests per minute
                window=60
            )
            
            if not is_allowed:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded for authentication endpoints"}
                )
        
        # Process request
        response = await call_next(request)
        return response

# Add middleware to FastAPI app
app.add_middleware(AuthenticationMiddleware, rate_limiter=rate_limiter)
```

## Role-Based Access Control (RBAC)

### Role Hierarchy

The system supports hierarchical roles:

1. **User** (Level 1) - Basic user permissions
2. **Moderator** (Level 2) - Content moderation permissions
3. **Admin** (Level 3) - User and system management permissions
4. **Superuser** (Level 4) - Full system access

### Permission System

Permissions follow a resource:action pattern:

```python
# User permissions
"user:read_own_profile"
"user:update_own_profile"
"user:delete_own_account"

# Content permissions
"content:read"
"content:create_own"
"content:update_own"
"content:delete_own"

# Admin permissions
"user:read_others_profile"
"user:update_others_profile"
"user:suspend_users"
"system:manage_settings"

# Wildcard permissions
"user:*"  # All user permissions
"admin:*"  # All admin permissions
```

### Usage in Code

```python
# Check specific permission
if current_user.has_permission("user:update_others_profile"):
    # Allow user profile update
    pass

# Check role-based access
if current_user.can_access_resource("admin", ["user:suspend_users"]):
    # Allow user suspension
    pass

# Check role hierarchy
if current_user.role.can_access_role("moderator"):
    # User can access moderator resources
    pass
```

## Security Features

### Account Lockout Protection

- Configurable maximum login attempts (default: 5)
- Automatic account lockout with configurable duration
- Progressive lockout periods for repeated violations
- Automatic unlock after lockout period expires

### Password Security

- Configurable password policies (length, complexity)
- Password breach detection using HaveIBeenPwned API
- Secure password hashing with bcrypt/scrypt/Argon2
- Password strength validation and scoring

### Rate Limiting

- IP-based rate limiting for authentication endpoints
- User-based rate limiting for sensitive operations
- Configurable limits and time windows
- Redis-backed rate limiting for scalability

### Security Logging

- Comprehensive security event logging
- Failed login attempt tracking
- Suspicious activity detection
- Geolocation tracking for login attempts
- Security event analysis and reporting

## Testing

The authentication system includes comprehensive tests:

```bash
# Run all authentication tests
pytest tests/unit/domain/test_user_entity.py
pytest tests/unit/application/test_auth_use_cases.py
pytest tests/integration/test_auth_endpoints.py

# Run with coverage
pytest --cov=src/domain/entities/user --cov=src/application/use_cases tests/
```

### Test Examples

```python
# Domain entity tests
def test_user_authentication_workflow():
    user = User(email=Email("test@example.com"))
    
    # Test failed login attempts
    user.record_login_attempt(success=False)
    assert user.failed_login_attempts == 1
    
    # Test account lockout
    for _ in range(4):
        user.record_login_attempt(success=False)
    
    user.lock_account()
    assert user.is_locked()
    
    # Test successful login resets attempts
    user.record_login_attempt(success=True)
    assert user.failed_login_attempts == 0

# Use case tests
@pytest.mark.asyncio
async def test_register_user_success():
    use_case = RegisterUserUseCase(...)
    request = RegisterUserRequest(
        email="test@example.com",
        password="SecurePass123!"
    )
    
    response = await use_case.execute(request)
    
    assert response.success is True
    assert response.user_id is not None
```

## Deployment Considerations

### Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Production Security

1. **Use strong secret keys** (64+ characters, cryptographically random)
2. **Enable HTTPS** for all authentication endpoints
3. **Configure secure cookies** (HttpOnly, Secure, SameSite)
4. **Set up proper CORS** policies
5. **Enable security headers** (HSTS, CSP, etc.)
6. **Monitor security events** and set up alerting
7. **Regular security audits** and dependency updates
8. **Database encryption** for sensitive data
9. **Rate limiting** at multiple layers (application, reverse proxy)
10. **Regular backup** and disaster recovery procedures

### Monitoring and Alerting

```python
# Example security monitoring
async def monitor_security_events():
    """Monitor and alert on security events."""
    
    # Check for suspicious login patterns
    suspicious_logins = await auth_service.get_security_events(
        event_type="login_failed",
        start_date=datetime.utcnow() - timedelta(hours=1)
    )
    
    if len(suspicious_logins) > 100:  # More than 100 failed logins in 1 hour
        await send_security_alert("High number of failed login attempts detected")
    
    # Check for account lockouts
    lockouts = await auth_service.get_security_events(
        event_type="account_locked",
        start_date=datetime.utcnow() - timedelta(hours=24)
    )
    
    if len(lockouts) > 50:  # More than 50 lockouts in 24 hours
        await send_security_alert("High number of account lockouts detected")
```

This authentication system provides enterprise-grade security while maintaining clean architecture principles and developer-friendly APIs.

