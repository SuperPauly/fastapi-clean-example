"""
Register User Use Case - Application Layer

This module contains the register user use case following
hexagonal architecture principles.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any

from ..ports.user_repository import UserRepositoryPort, UserAlreadyExistsError
from ..ports.authentication_service import AuthenticationServicePort
from ..ports.token_service import TokenServicePort
from ...domain.services.authentication_service import (
    AuthenticationDomainService,
    RegistrationResult
)
from ...domain.value_objects.email import Email
from ...domain.value_objects.password import PasswordPolicy


@dataclass
class RegisterUserRequest:
    """Request data for user registration."""
    email: str
    password: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = "user"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    recaptcha_response: Optional[str] = None


@dataclass
class RegisterUserResponse:
    """Response data for user registration."""
    success: bool
    user_id: Optional[int] = None
    email: Optional[str] = None
    requires_verification: bool = False
    verification_token: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None


class RegisterUserUseCase:
    """
    Use case for registering new users.
    
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
        require_email_verification: bool = True,
        require_recaptcha: bool = False
    ):
        """
        Initialize register user use case.
        
        Args:
            user_repository: User repository port
            auth_service: Authentication service port
            token_service: Token service port
            password_policy: Password policy to enforce
            require_email_verification: Whether email verification is required
            require_recaptcha: Whether reCAPTCHA validation is required
        """
        self.user_repository = user_repository
        self.auth_service = auth_service
        self.token_service = token_service
        self.domain_service = AuthenticationDomainService(password_policy)
        self.require_email_verification = require_email_verification
        self.require_recaptcha = require_recaptcha
    
    async def execute(self, request: RegisterUserRequest) -> RegisterUserResponse:
        """
        Execute user registration use case.
        
        Args:
            request: Registration request data
            
        Returns:
            RegisterUserResponse: Registration result
        """
        try:
            # Validate reCAPTCHA if required
            if self.require_recaptcha and request.recaptcha_response:
                is_valid_recaptcha = await self.auth_service.validate_recaptcha(
                    request.recaptcha_response
                )
                if not is_valid_recaptcha:
                    return RegisterUserResponse(
                        success=False,
                        error_message="reCAPTCHA validation failed",
                        error_code="INVALID_RECAPTCHA"
                    )
            
            # Check rate limiting for registration
            rate_limit_key = request.ip_address or "unknown"
            is_allowed, rate_info = await self.auth_service.check_rate_limit(
                identifier=rate_limit_key,
                action="register",
                limit=5,  # 5 registrations per hour
                window_seconds=3600
            )
            
            if not is_allowed:
                return RegisterUserResponse(
                    success=False,
                    error_message="Too many registration attempts. Please try again later.",
                    error_code="RATE_LIMIT_EXCEEDED"
                )
            
            # Check if email already exists
            try:
                email_obj = Email(request.email)
            except ValueError as e:
                return RegisterUserResponse(
                    success=False,
                    error_message=f"Invalid email format: {str(e)}",
                    error_code="INVALID_EMAIL"
                )
            
            if await self.user_repository.email_exists(email_obj):
                return RegisterUserResponse(
                    success=False,
                    error_message="An account with this email already exists",
                    error_code="EMAIL_EXISTS"
                )
            
            # Check if username already exists (if provided)
            if request.username and await self.user_repository.username_exists(request.username):
                return RegisterUserResponse(
                    success=False,
                    error_message="Username is already taken",
                    error_code="USERNAME_EXISTS"
                )
            
            # Check password against breach database
            is_breached = await self.auth_service.check_password_breach(request.password)
            if is_breached:
                return RegisterUserResponse(
                    success=False,
                    error_message="This password has been found in data breaches. Please choose a different password.",
                    error_code="PASSWORD_BREACHED"
                )
            
            # Register user using domain service
            registration_result = self.domain_service.register_user(
                email=request.email,
                password=request.password,
                username=request.username,
                first_name=request.first_name,
                last_name=request.last_name,
                role=request.role,
                require_verification=self.require_email_verification
            )
            
            if not registration_result.success:
                return RegisterUserResponse(
                    success=False,
                    error_message=registration_result.error_message,
                    error_code="REGISTRATION_FAILED"
                )
            
            # Begin transaction
            await self.user_repository.begin_transaction()
            
            try:
                # Create user in repository
                created_user = await self.user_repository.create_user(registration_result.user)
                
                # Store verification token if required
                verification_token_value = None
                if registration_result.verification_token:
                    # Update token with actual user ID
                    verification_token = registration_result.verification_token.add_metadata(
                        "user_id", created_user.id
                    )
                    
                    await self.token_service.create_token(
                        token_type=verification_token.token_type,
                        user_id=created_user.id,
                        expires_in=verification_token.get_remaining_lifetime(),
                        metadata=verification_token.metadata
                    )
                    
                    verification_token_value = verification_token.value
                    
                    # Send verification email
                    await self.auth_service.send_verification_email(
                        created_user,
                        verification_token
                    )
                
                # Send welcome email if email is already verified
                if created_user.is_verified:
                    await self.auth_service.send_welcome_email(created_user)
                
                # Log security event
                await self.auth_service.log_security_event(
                    user_id=created_user.id,
                    event_type="user_registered",
                    details={
                        "email": created_user.email.value,
                        "username": created_user.username,
                        "role": created_user.role.value,
                        "requires_verification": self.require_email_verification,
                        "registration_method": "email_password"
                    },
                    ip_address=request.ip_address,
                    user_agent=request.user_agent
                )
                
                # Increment rate limit counter
                await self.auth_service.increment_rate_limit(
                    identifier=rate_limit_key,
                    action="register",
                    window_seconds=3600
                )
                
                # Commit transaction
                await self.user_repository.commit_transaction()
                
                return RegisterUserResponse(
                    success=True,
                    user_id=created_user.id,
                    email=created_user.email.value,
                    requires_verification=self.require_email_verification,
                    verification_token=verification_token_value
                )
                
            except Exception as e:
                # Rollback transaction on error
                await self.user_repository.rollback_transaction()
                raise e
            
        except UserAlreadyExistsError:
            return RegisterUserResponse(
                success=False,
                error_message="An account with this email already exists",
                error_code="EMAIL_EXISTS"
            )
        
        except Exception as e:
            # Log unexpected error
            await self.auth_service.log_security_event(
                user_id=None,
                event_type="registration_error",
                details={
                    "error": str(e),
                    "email": request.email,
                    "username": request.username
                },
                ip_address=request.ip_address,
                user_agent=request.user_agent
            )
            
            return RegisterUserResponse(
                success=False,
                error_message="Registration failed due to an internal error",
                error_code="INTERNAL_ERROR"
            )
    
    async def resend_verification_email(
        self,
        email: str,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resend email verification email.
        
        Args:
            email: User email address
            ip_address: Client IP address
            
        Returns:
            Dictionary with operation result
        """
        try:
            # Check rate limiting for resend verification
            rate_limit_key = ip_address or "unknown"
            is_allowed, rate_info = await self.auth_service.check_rate_limit(
                identifier=rate_limit_key,
                action="resend_verification",
                limit=3,  # 3 resends per hour
                window_seconds=3600
            )
            
            if not is_allowed:
                return {
                    "success": False,
                    "error_message": "Too many verification email requests. Please try again later.",
                    "error_code": "RATE_LIMIT_EXCEEDED"
                }
            
            # Get user by email
            email_obj = Email(email)
            user = await self.user_repository.get_user_by_email(email_obj)
            
            if not user:
                # Don't reveal if email exists or not for security
                return {
                    "success": True,
                    "message": "If an account with this email exists and requires verification, a new verification email has been sent."
                }
            
            # Check if user already verified
            if user.is_verified:
                return {
                    "success": False,
                    "error_message": "Account is already verified",
                    "error_code": "ALREADY_VERIFIED"
                }
            
            # Generate new verification token
            verification_token = await self.token_service.create_token(
                token_type=self.token_service.TokenType.EMAIL_VERIFICATION,
                user_id=user.id,
                expires_in=timedelta(hours=24),
                metadata={"email": user.email.value}
            )
            
            # Send verification email
            await self.auth_service.send_verification_email(user, verification_token)
            
            # Log security event
            await self.auth_service.log_security_event(
                user_id=user.id,
                event_type="verification_email_resent",
                details={"email": user.email.value},
                ip_address=ip_address
            )
            
            # Increment rate limit counter
            await self.auth_service.increment_rate_limit(
                identifier=rate_limit_key,
                action="resend_verification",
                window_seconds=3600
            )
            
            return {
                "success": True,
                "message": "Verification email has been sent."
            }
            
        except Exception as e:
            # Log error
            await self.auth_service.log_security_event(
                user_id=None,
                event_type="resend_verification_error",
                details={"error": str(e), "email": email},
                ip_address=ip_address
            )
            
            return {
                "success": False,
                "error_message": "Failed to resend verification email",
                "error_code": "INTERNAL_ERROR"
            }

