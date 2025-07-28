"""
Tests for Authentication Use Cases - Application Layer

This module contains comprehensive tests for authentication use cases following
hexagonal architecture testing principles.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from src.application.use_cases.register_user import (
    RegisterUserUseCase,
    RegisterUserRequest,
    RegisterUserResponse
)
from src.application.use_cases.authenticate_user import (
    AuthenticateUserUseCase,
    AuthenticateUserRequest,
    AuthenticateUserResponse
)
from src.application.use_cases.social_login import (
    SocialLoginUseCase,
    SocialLoginRequest,
    SocialLoginResponse
)
from src.application.ports.user_repository import UserRepositoryPort, UserAlreadyExistsError
from src.application.ports.authentication_service import AuthenticationServicePort
from src.application.ports.token_service import TokenServicePort
from src.domain.entities.user import User, UserStatus
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import Password
from src.domain.value_objects.user_role import UserRole
from src.domain.value_objects.auth_token import AuthToken, TokenType


@pytest.fixture
def mock_user_repository():
    """Mock user repository."""
    repository = Mock(spec=UserRepositoryPort)
    repository.email_exists = AsyncMock(return_value=False)
    repository.username_exists = AsyncMock(return_value=False)
    repository.create_user = AsyncMock()
    repository.get_user_by_email = AsyncMock()
    repository.get_user_by_id = AsyncMock()
    repository.get_user_by_social_account = AsyncMock()
    repository.update_user = AsyncMock()
    repository.begin_transaction = AsyncMock()
    repository.commit_transaction = AsyncMock()
    repository.rollback_transaction = AsyncMock()
    return repository


@pytest.fixture
def mock_auth_service():
    """Mock authentication service."""
    service = Mock(spec=AuthenticationServicePort)
    service.validate_recaptcha = AsyncMock(return_value=True)
    service.check_rate_limit = AsyncMock(return_value=(True, {}))
    service.increment_rate_limit = AsyncMock()
    service.check_password_breach = AsyncMock(return_value=False)
    service.send_verification_email = AsyncMock(return_value=True)
    service.send_welcome_email = AsyncMock(return_value=True)
    service.send_login_notification = AsyncMock(return_value=True)
    service.log_security_event = AsyncMock()
    service.detect_suspicious_activity = AsyncMock(return_value={"score": 0, "is_suspicious": False})
    service.get_geolocation = AsyncMock(return_value={"country": "US"})
    service.validate_oauth_state = AsyncMock(return_value=True)
    service.generate_oauth_state = AsyncMock(return_value="state123")
    service.get_oauth_authorization_url = AsyncMock(return_value="https://oauth.provider.com/auth")
    service.exchange_oauth_code = AsyncMock(return_value={"access_token": "oauth_token"})
    service.get_oauth_user_info = AsyncMock(return_value={
        "id": "123456",
        "email": "user@example.com",
        "name": "John Doe",
        "given_name": "John",
        "family_name": "Doe"
    })
    return service


@pytest.fixture
def mock_token_service():
    """Mock token service."""
    service = Mock(spec=TokenServicePort)
    service.create_token = AsyncMock()
    service.validate_token = AsyncMock()
    service.revoke_token = AsyncMock(return_value=True)
    service.revoke_all_user_tokens = AsyncMock(return_value=2)
    service.log_token_usage = AsyncMock()
    service.TokenType = TokenType
    return service


@pytest.fixture
def sample_user():
    """Sample user for testing."""
    email = Email("test@example.com")
    password = Mock(spec=Password)
    password.verify_password.return_value = True
    
    user = User(
        id=1,
        email=email,
        password=password,
        username="testuser",
        first_name="Test",
        last_name="User",
        is_verified=True,
        is_active=True,
        status=UserStatus.ACTIVE,
        role=UserRole("user")
    )
    return user


class TestRegisterUserUseCase:
    """Test cases for RegisterUserUseCase."""
    
    @pytest.mark.asyncio
    async def test_successful_registration(self, mock_user_repository, mock_auth_service, mock_token_service):
        """Test successful user registration."""
        # Setup
        use_case = RegisterUserUseCase(
            user_repository=mock_user_repository,
            auth_service=mock_auth_service,
            token_service=mock_token_service,
            require_email_verification=True
        )
        
        created_user = Mock()
        created_user.id = 1
        created_user.email = Email("test@example.com")
        created_user.is_verified = False
        mock_user_repository.create_user.return_value = created_user
        
        verification_token = Mock(spec=AuthToken)
        verification_token.value = "verification_token_123"
        verification_token.token_type = TokenType.EMAIL_VERIFICATION
        verification_token.get_remaining_lifetime.return_value = timedelta(hours=24)
        verification_token.metadata = {"email": "test@example.com"}
        verification_token.add_metadata.return_value = verification_token
        mock_token_service.create_token.return_value = verification_token
        
        request = RegisterUserRequest(
            email="test@example.com",
            password="SecurePass123!",
            username="testuser",
            first_name="Test",
            last_name="User",
            ip_address="192.168.1.1",
            user_agent="TestAgent/1.0"
        )
        
        # Execute
        response = await use_case.execute(request)
        
        # Assert
        assert response.success is True
        assert response.user_id == 1
        assert response.email == "test@example.com"
        assert response.requires_verification is True
        assert response.verification_token == "verification_token_123"
        assert response.error_message is None
        
        # Verify interactions
        mock_user_repository.email_exists.assert_called_once()
        mock_user_repository.username_exists.assert_called_once()
        mock_user_repository.create_user.assert_called_once()
        mock_auth_service.send_verification_email.assert_called_once()
        mock_auth_service.log_security_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_registration_with_existing_email(self, mock_user_repository, mock_auth_service, mock_token_service):
        """Test registration with existing email."""
        # Setup
        use_case = RegisterUserUseCase(
            user_repository=mock_user_repository,
            auth_service=mock_auth_service,
            token_service=mock_token_service
        )
        
        mock_user_repository.email_exists.return_value = True
        
        request = RegisterUserRequest(
            email="existing@example.com",
            password="SecurePass123!"
        )
        
        # Execute
        response = await use_case.execute(request)
        
        # Assert
        assert response.success is False
        assert response.error_code == "EMAIL_EXISTS"
        assert "already exists" in response.error_message
    
    @pytest.mark.asyncio
    async def test_registration_with_weak_password(self, mock_user_repository, mock_auth_service, mock_token_service):
        """Test registration with weak password."""
        # Setup
        use_case = RegisterUserUseCase(
            user_repository=mock_user_repository,
            auth_service=mock_auth_service,
            token_service=mock_token_service
        )
        
        request = RegisterUserRequest(
            email="test@example.com",
            password="weak"  # Too short and simple
        )
        
        # Execute
        response = await use_case.execute(request)
        
        # Assert
        assert response.success is False
        assert response.error_code == "REGISTRATION_FAILED"
        assert "Password validation failed" in response.error_message
    
    @pytest.mark.asyncio
    async def test_registration_rate_limit_exceeded(self, mock_user_repository, mock_auth_service, mock_token_service):
        """Test registration with rate limit exceeded."""
        # Setup
        use_case = RegisterUserUseCase(
            user_repository=mock_user_repository,
            auth_service=mock_auth_service,
            token_service=mock_token_service
        )
        
        mock_auth_service.check_rate_limit.return_value = (False, {"remaining": 0})
        
        request = RegisterUserRequest(
            email="test@example.com",
            password="SecurePass123!",
            ip_address="192.168.1.1"
        )
        
        # Execute
        response = await use_case.execute(request)
        
        # Assert
        assert response.success is False
        assert response.error_code == "RATE_LIMIT_EXCEEDED"
        assert "Too many registration attempts" in response.error_message
    
    @pytest.mark.asyncio
    async def test_registration_with_breached_password(self, mock_user_repository, mock_auth_service, mock_token_service):
        """Test registration with breached password."""
        # Setup
        use_case = RegisterUserUseCase(
            user_repository=mock_user_repository,
            auth_service=mock_auth_service,
            token_service=mock_token_service
        )
        
        mock_auth_service.check_password_breach.return_value = True
        
        request = RegisterUserRequest(
            email="test@example.com",
            password="password123"  # Common breached password
        )
        
        # Execute
        response = await use_case.execute(request)
        
        # Assert
        assert response.success is False
        assert response.error_code == "PASSWORD_BREACHED"
        assert "found in data breaches" in response.error_message


class TestAuthenticateUserUseCase:
    """Test cases for AuthenticateUserUseCase."""
    
    @pytest.mark.asyncio
    async def test_successful_authentication(self, mock_user_repository, mock_auth_service, mock_token_service, sample_user):
        """Test successful user authentication."""
        # Setup
        use_case = AuthenticateUserUseCase(
            user_repository=mock_user_repository,
            auth_service=mock_auth_service,
            token_service=mock_token_service
        )
        
        mock_user_repository.get_user_by_email.return_value = sample_user
        
        access_token = Mock(spec=AuthToken)
        access_token.value = "access_token_123"
        refresh_token = Mock(spec=AuthToken)
        refresh_token.value = "refresh_token_123"
        
        mock_token_service.create_token.side_effect = [access_token, refresh_token]
        
        request = AuthenticateUserRequest(
            email="test@example.com",
            password="correct_password",
            ip_address="192.168.1.1",
            user_agent="TestAgent/1.0"
        )
        
        # Execute
        response = await use_case.execute(request)
        
        # Assert
        assert response.success is True
        assert response.user_id == 1
        assert response.access_token == "access_token_123"
        assert response.refresh_token == "refresh_token_123"
        assert response.token_type == "Bearer"
        assert response.user_info is not None
        assert response.user_info["email"] == "test@example.com"
        
        # Verify interactions
        mock_user_repository.get_user_by_email.assert_called_once()
        mock_user_repository.update_user.assert_called_once()
        mock_auth_service.log_security_event.assert_called_once()
        mock_token_service.log_token_usage.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authentication_with_invalid_email(self, mock_user_repository, mock_auth_service, mock_token_service):
        """Test authentication with invalid email."""
        # Setup
        use_case = AuthenticateUserUseCase(
            user_repository=mock_user_repository,
            auth_service=mock_auth_service,
            token_service=mock_token_service
        )
        
        request = AuthenticateUserRequest(
            email="invalid-email",
            password="password"
        )
        
        # Execute
        response = await use_case.execute(request)
        
        # Assert
        assert response.success is False
        assert response.error_code == "INVALID_EMAIL"
        assert "Invalid email format" in response.error_message
    
    @pytest.mark.asyncio
    async def test_authentication_with_nonexistent_user(self, mock_user_repository, mock_auth_service, mock_token_service):
        """Test authentication with non-existent user."""
        # Setup
        use_case = AuthenticateUserUseCase(
            user_repository=mock_user_repository,
            auth_service=mock_auth_service,
            token_service=mock_token_service
        )
        
        mock_user_repository.get_user_by_email.return_value = None
        
        request = AuthenticateUserRequest(
            email="nonexistent@example.com",
            password="password"
        )
        
        # Execute
        response = await use_case.execute(request)
        
        # Assert
        assert response.success is False
        assert response.error_code == "INVALID_CREDENTIALS"
        assert "Invalid email or password" in response.error_message
        
        # Verify security logging
        mock_auth_service.log_security_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authentication_with_wrong_password(self, mock_user_repository, mock_auth_service, mock_token_service, sample_user):
        """Test authentication with wrong password."""
        # Setup
        use_case = AuthenticateUserUseCase(
            user_repository=mock_user_repository,
            auth_service=mock_auth_service,
            token_service=mock_token_service
        )
        
        sample_user.password.verify_password.return_value = False
        mock_user_repository.get_user_by_email.return_value = sample_user
        
        request = AuthenticateUserRequest(
            email="test@example.com",
            password="wrong_password"
        )
        
        # Execute
        response = await use_case.execute(request)
        
        # Assert
        assert response.success is False
        assert response.error_code == "AUTHENTICATION_FAILED"
        assert "Invalid password" in response.error_message
        
        # Verify failed attempt was recorded
        mock_user_repository.update_user.assert_called_once()
        mock_auth_service.log_security_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authentication_with_locked_account(self, mock_user_repository, mock_auth_service, mock_token_service, sample_user):
        """Test authentication with locked account."""
        # Setup
        use_case = AuthenticateUserUseCase(
            user_repository=mock_user_repository,
            auth_service=mock_auth_service,
            token_service=mock_token_service
        )
        
        sample_user.status = UserStatus.LOCKED
        sample_user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        mock_user_repository.get_user_by_email.return_value = sample_user
        
        request = AuthenticateUserRequest(
            email="test@example.com",
            password="correct_password"
        )
        
        # Execute
        response = await use_case.execute(request)
        
        # Assert
        assert response.success is False
        assert response.account_locked is True
        assert response.lockout_expires_at is not None
        assert "temporarily locked" in response.error_message
    
    @pytest.mark.asyncio
    async def test_logout_success(self, mock_user_repository, mock_auth_service, mock_token_service):
        """Test successful logout."""
        # Setup
        use_case = AuthenticateUserUseCase(
            user_repository=mock_user_repository,
            auth_service=mock_auth_service,
            token_service=mock_token_service
        )
        
        token = Mock(spec=AuthToken)
        token.user_id = 1
        mock_token_service.validate_token.return_value = token
        
        # Execute
        result = await use_case.logout(
            access_token="access_token_123",
            refresh_token="refresh_token_456",
            ip_address="192.168.1.1"
        )
        
        # Assert
        assert result["success"] is True
        assert result["tokens_revoked"] == 2
        
        # Verify interactions
        mock_token_service.revoke_token.assert_called()
        mock_auth_service.log_security_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, mock_user_repository, mock_auth_service, mock_token_service, sample_user):
        """Test successful token refresh."""
        # Setup
        use_case = AuthenticateUserUseCase(
            user_repository=mock_user_repository,
            auth_service=mock_auth_service,
            token_service=mock_token_service
        )
        
        refresh_token = Mock(spec=AuthToken)
        refresh_token.user_id = 1
        refresh_token.get_hash.return_value = "token_hash"
        mock_token_service.validate_token.return_value = refresh_token
        mock_user_repository.get_user_by_id.return_value = sample_user
        
        new_access_token = Mock(spec=AuthToken)
        new_access_token.value = "new_access_token_123"
        mock_token_service.create_token.return_value = new_access_token
        
        # Execute
        result = await use_case.refresh_access_token(
            refresh_token="refresh_token_123",
            ip_address="192.168.1.1"
        )
        
        # Assert
        assert result["success"] is True
        assert result["access_token"] == "new_access_token_123"
        assert result["token_type"] == "Bearer"
        
        # Verify interactions
        mock_token_service.validate_token.assert_called_once()
        mock_user_repository.get_user_by_id.assert_called_once()
        mock_token_service.create_token.assert_called_once()


class TestSocialLoginUseCase:
    """Test cases for SocialLoginUseCase."""
    
    @pytest.mark.asyncio
    async def test_get_authorization_url(self, mock_user_repository, mock_auth_service, mock_token_service):
        """Test getting OAuth authorization URL."""
        # Setup
        use_case = SocialLoginUseCase(
            user_repository=mock_user_repository,
            auth_service=mock_auth_service,
            token_service=mock_token_service
        )
        
        # Execute
        result = await use_case.get_authorization_url(
            provider="google",
            redirect_uri="http://localhost:8000/auth/callback",
            scopes=["email", "profile"]
        )
        
        # Assert
        assert result["success"] is True
        assert result["authorization_url"] == "https://oauth.provider.com/auth"
        assert result["state"] == "state123"
        assert result["provider"] == "google"
        
        # Verify interactions
        mock_auth_service.generate_oauth_state.assert_called_once()
        mock_auth_service.get_oauth_authorization_url.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_social_login_new_user(self, mock_user_repository, mock_auth_service, mock_token_service):
        """Test social login with new user creation."""
        # Setup
        use_case = SocialLoginUseCase(
            user_repository=mock_user_repository,
            auth_service=mock_auth_service,
            token_service=mock_token_service,
            auto_create_users=True
        )
        
        mock_user_repository.get_user_by_social_account.return_value = None
        mock_user_repository.get_user_by_email.return_value = None
        
        created_user = Mock()
        created_user.id = 1
        created_user.email = Email("user@example.com")
        created_user.username = "johndoe"
        created_user.first_name = "John"
        created_user.last_name = "Doe"
        created_user.display_name = "John Doe"
        created_user.avatar_url = None
        created_user.role = UserRole("user")
        created_user.permissions = []
        created_user.is_verified = True
        created_user.is_active = True
        created_user.status = UserStatus.ACTIVE
        created_user.social_accounts = [{"provider": "google"}]
        created_user.record_login_attempt = Mock()
        mock_user_repository.create_user.return_value = created_user
        
        access_token = Mock(spec=AuthToken)
        access_token.value = "access_token_123"
        refresh_token = Mock(spec=AuthToken)
        refresh_token.value = "refresh_token_123"
        mock_token_service.create_token.side_effect = [access_token, refresh_token]
        
        request = SocialLoginRequest(
            provider="google",
            access_token="oauth_access_token",
            ip_address="192.168.1.1",
            user_agent="TestAgent/1.0"
        )
        
        # Execute
        response = await use_case.execute(request)
        
        # Assert
        assert response.success is True
        assert response.user_id == 1
        assert response.is_new_user is True
        assert response.access_token == "access_token_123"
        assert response.refresh_token == "refresh_token_123"
        assert response.user_info is not None
        
        # Verify interactions
        mock_user_repository.create_user.assert_called_once()
        mock_auth_service.send_welcome_email.assert_called_once()
        mock_auth_service.log_security_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_social_login_existing_user(self, mock_user_repository, mock_auth_service, mock_token_service, sample_user):
        """Test social login with existing user."""
        # Setup
        use_case = SocialLoginUseCase(
            user_repository=mock_user_repository,
            auth_service=mock_auth_service,
            token_service=mock_token_service
        )
        
        sample_user.social_accounts = [{"provider": "google", "provider_id": "123456"}]
        sample_user.record_login_attempt = Mock()
        sample_user.add_social_account = Mock()
        sample_user.update_profile = Mock()
        mock_user_repository.get_user_by_social_account.return_value = sample_user
        
        access_token = Mock(spec=AuthToken)
        access_token.value = "access_token_123"
        refresh_token = Mock(spec=AuthToken)
        refresh_token.value = "refresh_token_123"
        mock_token_service.create_token.side_effect = [access_token, refresh_token]
        
        request = SocialLoginRequest(
            provider="google",
            access_token="oauth_access_token",
            ip_address="192.168.1.1"
        )
        
        # Execute
        response = await use_case.execute(request)
        
        # Assert
        assert response.success is True
        assert response.user_id == 1
        assert response.is_new_user is False
        assert response.access_token == "access_token_123"
        
        # Verify interactions
        mock_user_repository.update_user.assert_called()
        mock_auth_service.log_security_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_social_login_unsupported_provider(self, mock_user_repository, mock_auth_service, mock_token_service):
        """Test social login with unsupported provider."""
        # Setup
        use_case = SocialLoginUseCase(
            user_repository=mock_user_repository,
            auth_service=mock_auth_service,
            token_service=mock_token_service
        )
        
        request = SocialLoginRequest(
            provider="unsupported_provider",
            access_token="oauth_access_token"
        )
        
        # Execute
        response = await use_case.execute(request)
        
        # Assert
        assert response.success is False
        assert response.error_code == "UNSUPPORTED_PROVIDER"
        assert "Unsupported OAuth provider" in response.error_message
    
    @pytest.mark.asyncio
    async def test_social_login_rate_limit_exceeded(self, mock_user_repository, mock_auth_service, mock_token_service):
        """Test social login with rate limit exceeded."""
        # Setup
        use_case = SocialLoginUseCase(
            user_repository=mock_user_repository,
            auth_service=mock_auth_service,
            token_service=mock_token_service
        )
        
        mock_auth_service.check_rate_limit.return_value = (False, {"remaining": 0})
        
        request = SocialLoginRequest(
            provider="google",
            access_token="oauth_access_token",
            ip_address="192.168.1.1"
        )
        
        # Execute
        response = await use_case.execute(request)
        
        # Assert
        assert response.success is False
        assert response.error_code == "RATE_LIMIT_EXCEEDED"
        assert "Too many social login attempts" in response.error_message
    
    @pytest.mark.asyncio
    async def test_link_social_account_success(self, mock_user_repository, mock_auth_service, mock_token_service, sample_user):
        """Test successful social account linking."""
        # Setup
        use_case = SocialLoginUseCase(
            user_repository=mock_user_repository,
            auth_service=mock_auth_service,
            token_service=mock_token_service
        )
        
        mock_user_repository.get_user_by_id.return_value = sample_user
        mock_user_repository.get_user_by_social_account.return_value = None
        
        # Execute
        result = await use_case.link_social_account(
            user_id=1,
            provider="github",
            access_token="oauth_access_token",
            ip_address="192.168.1.1"
        )
        
        # Assert
        assert result["success"] is True
        assert "linked successfully" in result["message"]
        assert result["provider"] == "github"
        
        # Verify interactions
        mock_user_repository.update_user.assert_called_once()
        mock_auth_service.log_security_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_unlink_social_account_success(self, mock_user_repository, mock_auth_service, mock_token_service, sample_user):
        """Test successful social account unlinking."""
        # Setup
        use_case = SocialLoginUseCase(
            user_repository=mock_user_repository,
            auth_service=mock_auth_service,
            token_service=mock_token_service
        )
        
        sample_user.password = Mock(spec=Password)  # User has password auth
        sample_user.social_accounts = [
            {"provider": "google", "provider_id": "123"},
            {"provider": "github", "provider_id": "456"}
        ]
        mock_user_repository.get_user_by_id.return_value = sample_user
        
        # Execute
        result = await use_case.unlink_social_account(
            user_id=1,
            provider="google",
            ip_address="192.168.1.1"
        )
        
        # Assert
        assert result["success"] is True
        assert "unlinked successfully" in result["message"]
        assert result["provider"] == "google"
        
        # Verify interactions
        mock_user_repository.update_user.assert_called_once()
        mock_auth_service.log_security_event.assert_called_once()

