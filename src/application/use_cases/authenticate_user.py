"""
Authenticate User Use Case - Application Layer

This module contains the authenticate user use case following
hexagonal architecture principles.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import timedelta

from ..ports.user_repository import UserRepositoryPort
from ..ports.authentication_service import AuthenticationServicePort
from ..ports.token_service import TokenServicePort
from ...domain.services.authentication_service import (
    AuthenticationDomainService,
    AuthenticationResult
)
from ...domain.value_objects.email import Email
from ...domain.value_objects.password import PasswordPolicy


@dataclass
class AuthenticateUserRequest:
    """Request data for user authentication."""
    email: str
    password: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    remember_me: bool = False
    recaptcha_response: Optional[str] = None


@dataclass
class AuthenticateUserResponse:
    """Response data for user authentication."""
    success: bool
    user_id: Optional[int] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    session_token: Optional[str] = None
    expires_in: Optional[int] = None
    token_type: str = "Bearer"
    requires_verification: bool = False
    account_locked: bool = False
    lockout_expires_at: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    user_info: Optional[Dict[str, Any]] = None


class AuthenticateUserUseCase:
    """
    Use case for authenticating users.
    
    This use case follows hexagonal architecture principles by:
    - Orchestrating domain services and entities
    - Using ports for external dependencies
    - Containing application-specific business logic
    - Being framework-agnostic
    """
    
    def __init__(
        self,
        user_repository: UserRepositoryPort,
        auth_service: AuthenticationServicePort,
        token_service: TokenServicePort,
        password_policy: Optional[PasswordPolicy] = None,
        max_login_attempts: int = 5,
        lockout_duration_minutes: int = 30,
        require_recaptcha_after_failures: int = 3
    ):
        """
        Initialize authenticate user use case.
        
        Args:
            user_repository: User repository port
            auth_service: Authentication service port
            token_service: Token service port
            password_policy: Password policy
            max_login_attempts: Maximum failed login attempts before lockout
            lockout_duration_minutes: Account lockout duration in minutes
            require_recaptcha_after_failures: Require reCAPTCHA after N failures
        """
        self.user_repository = user_repository
        self.auth_service = auth_service
        self.token_service = token_service
        self.domain_service = AuthenticationDomainService(password_policy)
        self.max_login_attempts = max_login_attempts
        self.lockout_duration_minutes = lockout_duration_minutes
        self.require_recaptcha_after_failures = require_recaptcha_after_failures
    
    async def execute(self, request: AuthenticateUserRequest) -> AuthenticateUserResponse:
        """
        Execute user authentication use case.
        
        Args:
            request: Authentication request data
            
        Returns:
            AuthenticateUserResponse: Authentication result
        """
        try:
            # Check rate limiting for login attempts
            rate_limit_key = request.ip_address or "unknown"
            is_allowed, rate_info = await self.auth_service.check_rate_limit(
                identifier=rate_limit_key,
                action="login",
                limit=10,  # 10 login attempts per 15 minutes
                window_seconds=900
            )
            
            if not is_allowed:
                return AuthenticateUserResponse(
                    success=False,
                    error_message="Too many login attempts. Please try again later.",
                    error_code="RATE_LIMIT_EXCEEDED"
                )
            
            # Validate email format
            try:
                email_obj = Email(request.email)
            except ValueError as e:
                return AuthenticateUserResponse(
                    success=False,
                    error_message=f"Invalid email format: {str(e)}",
                    error_code="INVALID_EMAIL"
                )
            
            # Get user by email
            user = await self.user_repository.get_user_by_email(email_obj)
            
            if not user:
                # Increment rate limit counter even for non-existent users
                await self.auth_service.increment_rate_limit(
                    identifier=rate_limit_key,
                    action="login",
                    window_seconds=900
                )
                
                # Log failed login attempt
                await self.auth_service.log_security_event(
                    user_id=None,
                    event_type="login_failed_user_not_found",
                    details={"email": request.email},
                    ip_address=request.ip_address,
                    user_agent=request.user_agent
                )
                
                return AuthenticateUserResponse(
                    success=False,
                    error_message="Invalid email or password",
                    error_code="INVALID_CREDENTIALS"
                )
            
            # Check if reCAPTCHA is required based on failed attempts
            if (user.failed_login_attempts >= self.require_recaptcha_after_failures 
                and request.recaptcha_response):
                is_valid_recaptcha = await self.auth_service.validate_recaptcha(
                    request.recaptcha_response
                )
                if not is_valid_recaptcha:
                    return AuthenticateUserResponse(
                        success=False,
                        error_message="reCAPTCHA validation failed",
                        error_code="INVALID_RECAPTCHA"
                    )
            
            # Detect suspicious activity
            suspicion_analysis = await self.auth_service.detect_suspicious_activity(
                user_id=user.id,
                ip_address=request.ip_address or "",
                user_agent=request.user_agent or ""
            )
            
            # Authenticate user using domain service
            auth_result = self.domain_service.authenticate_user(
                user=user,
                password=request.password,
                ip_address=request.ip_address,
                max_login_attempts=self.max_login_attempts,
                lockout_duration_minutes=self.lockout_duration_minutes
            )
            
            # Handle authentication failure
            if not auth_result.success:
                # Update user in repository
                await self.user_repository.update_user(user)
                
                # Increment rate limit counter
                await self.auth_service.increment_rate_limit(
                    identifier=rate_limit_key,
                    action="login",
                    window_seconds=900
                )
                
                # Log failed login attempt
                await self.auth_service.log_security_event(
                    user_id=user.id,
                    event_type="login_failed",
                    details={
                        "email": user.email.value,
                        "reason": auth_result.error_message,
                        "failed_attempts": user.failed_login_attempts,
                        "suspicion_score": suspicion_analysis.get("score", 0)
                    },
                    ip_address=request.ip_address,
                    user_agent=request.user_agent
                )
                
                return AuthenticateUserResponse(
                    success=False,
                    error_message=auth_result.error_message,
                    error_code="AUTHENTICATION_FAILED",
                    requires_verification=auth_result.requires_verification,
                    account_locked=auth_result.account_locked,
                    lockout_expires_at=(
                        auth_result.lockout_expires_at.isoformat() 
                        if auth_result.lockout_expires_at else None
                    )
                )
            
            # Successful authentication
            # Update user in repository
            await self.user_repository.update_user(user)
            
            # Create tokens
            access_token_expires = timedelta(minutes=30)
            refresh_token_expires = timedelta(days=7 if not request.remember_me else 30)
            
            access_token = await self.token_service.create_token(
                token_type=self.token_service.TokenType.ACCESS,
                user_id=user.id,
                expires_in=access_token_expires,
                metadata={
                    "role": user.role.value,
                    "permissions": list(user.permissions),
                    "ip_address": request.ip_address,
                    "user_agent": request.user_agent,
                    "suspicion_score": suspicion_analysis.get("score", 0)
                }
            )
            
            refresh_token = await self.token_service.create_token(
                token_type=self.token_service.TokenType.REFRESH,
                user_id=user.id,
                expires_in=refresh_token_expires,
                metadata={
                    "ip_address": request.ip_address,
                    "remember_me": request.remember_me
                }
            )
            
            # Create session token if requested
            session_token = None
            if request.remember_me:
                session_token = await self.token_service.create_session_token(
                    user_id=user.id,
                    session_data={
                        "login_time": user.last_login_at.isoformat() if user.last_login_at else None,
                        "ip_address": request.ip_address,
                        "user_agent": request.user_agent
                    },
                    expires_in_hours=24 * 30  # 30 days for remember me
                )
            
            # Send login notification if suspicious activity detected
            if suspicion_analysis.get("is_suspicious", False):
                await self.auth_service.send_login_notification(
                    user=user,
                    ip_address=request.ip_address or "",
                    user_agent=request.user_agent or ""
                )
            
            # Log successful login
            await self.auth_service.log_security_event(
                user_id=user.id,
                event_type="login_successful",
                details={
                    "email": user.email.value,
                    "role": user.role.value,
                    "remember_me": request.remember_me,
                    "suspicion_score": suspicion_analysis.get("score", 0),
                    "geolocation": await self.auth_service.get_geolocation(
                        request.ip_address or ""
                    )
                },
                ip_address=request.ip_address,
                user_agent=request.user_agent
            )
            
            # Log token usage
            await self.token_service.log_token_usage(
                token=access_token,
                action="login",
                ip_address=request.ip_address,
                user_agent=request.user_agent,
                additional_data={"remember_me": request.remember_me}
            )
            
            # Get user capabilities
            user_capabilities = self.domain_service.get_user_capabilities(user)
            
            return AuthenticateUserResponse(
                success=True,
                user_id=user.id,
                access_token=access_token.value,
                refresh_token=refresh_token.value,
                session_token=session_token.value if session_token else None,
                expires_in=int(access_token_expires.total_seconds()),
                token_type="Bearer",
                user_info={
                    "id": user.id,
                    "email": user.email.value,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "display_name": user.display_name,
                    "avatar_url": user.avatar_url,
                    "role": user.role.value,
                    "permissions": list(user.permissions),
                    "is_verified": user.is_verified,
                    "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                    "capabilities": user_capabilities
                }
            )
            
        except Exception as e:
            # Log unexpected error
            await self.auth_service.log_security_event(
                user_id=None,
                event_type="login_error",
                details={
                    "error": str(e),
                    "email": request.email
                },
                ip_address=request.ip_address,
                user_agent=request.user_agent
            )
            
            return AuthenticateUserResponse(
                success=False,
                error_message="Authentication failed due to an internal error",
                error_code="INTERNAL_ERROR"
            )
    
    async def logout(
        self,
        access_token: str,
        refresh_token: Optional[str] = None,
        revoke_all_tokens: bool = False,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Logout user by revoking tokens.
        
        Args:
            access_token: Access token to revoke
            refresh_token: Optional refresh token to revoke
            revoke_all_tokens: Whether to revoke all user tokens
            ip_address: Client IP address
            user_agent: User agent string
            
        Returns:
            Dictionary with logout result
        """
        try:
            # Validate access token
            token = await self.token_service.validate_token(access_token)
            if not token:
                return {
                    "success": False,
                    "error_message": "Invalid access token",
                    "error_code": "INVALID_TOKEN"
                }
            
            user_id = token.user_id
            
            # Revoke tokens
            if revoke_all_tokens:
                revoked_count = await self.token_service.revoke_all_user_tokens(
                    user_id=user_id
                )
            else:
                # Revoke specific tokens
                await self.token_service.revoke_token(access_token)
                revoked_count = 1
                
                if refresh_token:
                    await self.token_service.revoke_token(refresh_token)
                    revoked_count += 1
            
            # Log logout event
            await self.auth_service.log_security_event(
                user_id=user_id,
                event_type="logout",
                details={
                    "revoke_all_tokens": revoke_all_tokens,
                    "tokens_revoked": revoked_count
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return {
                "success": True,
                "message": "Logout successful",
                "tokens_revoked": revoked_count
            }
            
        except Exception as e:
            # Log error
            await self.auth_service.log_security_event(
                user_id=None,
                event_type="logout_error",
                details={"error": str(e)},
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return {
                "success": False,
                "error_message": "Logout failed due to an internal error",
                "error_code": "INTERNAL_ERROR"
            }
    
    async def refresh_access_token(
        self,
        refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token
            ip_address: Client IP address
            user_agent: User agent string
            
        Returns:
            Dictionary with new access token or error
        """
        try:
            # Validate refresh token
            token = await self.token_service.validate_token(
                refresh_token,
                expected_type=self.token_service.TokenType.REFRESH
            )
            
            if not token:
                return {
                    "success": False,
                    "error_message": "Invalid or expired refresh token",
                    "error_code": "INVALID_REFRESH_TOKEN"
                }
            
            # Get user
            user = await self.user_repository.get_user_by_id(token.user_id)
            if not user:
                return {
                    "success": False,
                    "error_message": "User not found",
                    "error_code": "USER_NOT_FOUND"
                }
            
            # Check if user is still active
            if not user.is_active:
                return {
                    "success": False,
                    "error_message": "User account is not active",
                    "error_code": "ACCOUNT_INACTIVE"
                }
            
            # Create new access token
            new_access_token = await self.token_service.create_token(
                token_type=self.token_service.TokenType.ACCESS,
                user_id=user.id,
                expires_in=timedelta(minutes=30),
                metadata={
                    "role": user.role.value,
                    "permissions": list(user.permissions),
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "refreshed_from": token.get_hash()
                }
            )
            
            # Log token refresh
            await self.auth_service.log_security_event(
                user_id=user.id,
                event_type="token_refreshed",
                details={
                    "email": user.email.value,
                    "refresh_token_hash": token.get_hash()
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Log token usage
            await self.token_service.log_token_usage(
                token=new_access_token,
                action="refresh",
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return {
                "success": True,
                "access_token": new_access_token.value,
                "token_type": "Bearer",
                "expires_in": int(timedelta(minutes=30).total_seconds())
            }
            
        except Exception as e:
            # Log error
            await self.auth_service.log_security_event(
                user_id=None,
                event_type="token_refresh_error",
                details={"error": str(e)},
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return {
                "success": False,
                "error_message": "Token refresh failed due to an internal error",
                "error_code": "INTERNAL_ERROR"
            }

