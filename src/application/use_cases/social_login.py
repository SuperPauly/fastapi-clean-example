"""
Social Login Use Case - Application Layer

This module contains the social login use case following
hexagonal architecture principles.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import timedelta

from ..ports.user_repository import UserRepositoryPort
from ..ports.authentication_service import AuthenticationServicePort
from ..ports.token_service import TokenServicePort
from ...domain.services.authentication_service import AuthenticationDomainService
from ...domain.value_objects.email import Email
from ...domain.value_objects.user_role import UserRole
from ...domain.entities.user import User, UserStatus


@dataclass
class SocialLoginRequest:
    """Request data for social login."""
    provider: str
    authorization_code: Optional[str] = None
    access_token: Optional[str] = None
    redirect_uri: Optional[str] = None
    state: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class SocialLoginResponse:
    """Response data for social login."""
    success: bool
    user_id: Optional[int] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    token_type: str = "Bearer"
    is_new_user: bool = False
    requires_profile_completion: bool = False
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    user_info: Optional[Dict[str, Any]] = None


class SocialLoginUseCase:
    """
    Use case for social authentication.
    
    This use case follows hexagonal architecture principles by:
    - Orchestrating domain services and entities
    - Using ports for external dependencies
    - Containing application-specific business logic
    - Being framework-agnostic
    """
    
    # Supported OAuth providers
    SUPPORTED_PROVIDERS = {
        "google", "github", "facebook", "twitter", "linkedin", 
        "microsoft", "steam", "twilio", "twitch", "spotify", 
        "stackoverflow", "instagram", "dropbox"
    }
    
    def __init__(
        self,
        user_repository: UserRepositoryPort,
        auth_service: AuthenticationServicePort,
        token_service: TokenServicePort,
        auto_create_users: bool = True,
        require_email_verification: bool = False
    ):
        """
        Initialize social login use case.
        
        Args:
            user_repository: User repository port
            auth_service: Authentication service port
            token_service: Token service port
            auto_create_users: Whether to automatically create users
            require_email_verification: Whether email verification is required
        """
        self.user_repository = user_repository
        self.auth_service = auth_service
        self.token_service = token_service
        self.domain_service = AuthenticationDomainService()
        self.auto_create_users = auto_create_users
        self.require_email_verification = require_email_verification
    
    async def get_authorization_url(
        self,
        provider: str,
        redirect_uri: str,
        scopes: Optional[List[str]] = None,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get OAuth authorization URL for provider.
        
        Args:
            provider: OAuth provider name
            redirect_uri: Redirect URI after authorization
            scopes: Optional list of scopes to request
            state: Optional state parameter
            
        Returns:
            Dictionary with authorization URL and state
        """
        try:
            if provider not in self.SUPPORTED_PROVIDERS:
                return {
                    "success": False,
                    "error_message": f"Unsupported OAuth provider: {provider}",
                    "error_code": "UNSUPPORTED_PROVIDER"
                }
            
            # Generate state if not provided
            if not state:
                state = await self.auth_service.generate_oauth_state()
            
            # Get authorization URL
            auth_url = await self.auth_service.get_oauth_authorization_url(
                provider=provider,
                redirect_uri=redirect_uri,
                state=state,
                scopes=scopes
            )
            
            return {
                "success": True,
                "authorization_url": auth_url,
                "state": state,
                "provider": provider
            }
            
        except Exception as e:
            return {
                "success": False,
                "error_message": f"Failed to get authorization URL: {str(e)}",
                "error_code": "AUTHORIZATION_URL_ERROR"
            }
    
    async def execute(self, request: SocialLoginRequest) -> SocialLoginResponse:
        """
        Execute social login use case.
        
        Args:
            request: Social login request data
            
        Returns:
            SocialLoginResponse: Social login result
        """
        try:
            # Validate provider
            if request.provider not in self.SUPPORTED_PROVIDERS:
                return SocialLoginResponse(
                    success=False,
                    error_message=f"Unsupported OAuth provider: {request.provider}",
                    error_code="UNSUPPORTED_PROVIDER"
                )
            
            # Check rate limiting for social login
            rate_limit_key = request.ip_address or "unknown"
            is_allowed, rate_info = await self.auth_service.check_rate_limit(
                identifier=rate_limit_key,
                action="social_login",
                limit=10,  # 10 social login attempts per 15 minutes
                window_seconds=900
            )
            
            if not is_allowed:
                return SocialLoginResponse(
                    success=False,
                    error_message="Too many social login attempts. Please try again later.",
                    error_code="RATE_LIMIT_EXCEEDED"
                )
            
            # Validate OAuth state if provided
            if request.state and not await self.auth_service.validate_oauth_state(request.state):
                return SocialLoginResponse(
                    success=False,
                    error_message="Invalid OAuth state parameter",
                    error_code="INVALID_OAUTH_STATE"
                )
            
            # Exchange authorization code for access token if needed
            oauth_access_token = request.access_token
            if request.authorization_code and not oauth_access_token:
                token_response = await self.auth_service.exchange_oauth_code(
                    provider=request.provider,
                    code=request.authorization_code,
                    redirect_uri=request.redirect_uri or ""
                )
                
                if not token_response:
                    return SocialLoginResponse(
                        success=False,
                        error_message="Failed to exchange authorization code for access token",
                        error_code="OAUTH_TOKEN_EXCHANGE_FAILED"
                    )
                
                oauth_access_token = token_response.get("access_token")
            
            if not oauth_access_token:
                return SocialLoginResponse(
                    success=False,
                    error_message="No OAuth access token provided",
                    error_code="MISSING_OAUTH_TOKEN"
                )
            
            # Get user information from OAuth provider
            user_info = await self.auth_service.get_oauth_user_info(
                provider=request.provider,
                access_token=oauth_access_token
            )
            
            if not user_info:
                return SocialLoginResponse(
                    success=False,
                    error_message="Failed to get user information from OAuth provider",
                    error_code="OAUTH_USER_INFO_FAILED"
                )
            
            # Extract user data from provider response
            provider_id = str(user_info.get("id") or user_info.get("sub"))
            email = user_info.get("email")
            username = user_info.get("username") or user_info.get("login")
            first_name = user_info.get("given_name") or user_info.get("first_name")
            last_name = user_info.get("family_name") or user_info.get("last_name")
            display_name = user_info.get("name") or user_info.get("display_name")
            avatar_url = user_info.get("picture") or user_info.get("avatar_url")
            
            if not provider_id:
                return SocialLoginResponse(
                    success=False,
                    error_message="Provider did not return user ID",
                    error_code="MISSING_PROVIDER_USER_ID"
                )
            
            if not email:
                return SocialLoginResponse(
                    success=False,
                    error_message="Provider did not return user email",
                    error_code="MISSING_USER_EMAIL"
                )
            
            # Check if user exists by social account
            existing_user = await self.user_repository.get_user_by_social_account(
                provider=request.provider,
                provider_id=provider_id
            )
            
            if existing_user:
                # User exists with this social account
                user = existing_user
                is_new_user = False
                
                # Update social account data
                user.add_social_account(request.provider, provider_id, user_info)
                
                # Update user profile if needed
                if not user.avatar_url and avatar_url:
                    user.update_profile(avatar_url=avatar_url)
                
                await self.user_repository.update_user(user)
                
            else:
                # Check if user exists by email
                try:
                    email_obj = Email(email)
                    existing_user_by_email = await self.user_repository.get_user_by_email(email_obj)
                    
                    if existing_user_by_email:
                        # Link social account to existing user
                        user = existing_user_by_email
                        is_new_user = False
                        
                        # Link social account
                        success = self.domain_service.link_social_account(
                            user=user,
                            provider=request.provider,
                            provider_id=provider_id,
                            profile_data=user_info
                        )
                        
                        if not success:
                            return SocialLoginResponse(
                                success=False,
                                error_message="Failed to link social account to existing user",
                                error_code="SOCIAL_ACCOUNT_LINK_FAILED"
                            )
                        
                        await self.user_repository.update_user(user)
                        
                    else:
                        # Create new user if auto-creation is enabled
                        if not self.auto_create_users:
                            return SocialLoginResponse(
                                success=False,
                                error_message="User does not exist and auto-creation is disabled",
                                error_code="USER_NOT_FOUND"
                            )
                        
                        # Validate social login data and create user
                        is_new, new_user, error_msg = self.domain_service.validate_social_login(
                            provider=request.provider,
                            provider_id=provider_id,
                            email=email,
                            profile_data={
                                "username": username,
                                "first_name": first_name,
                                "last_name": last_name,
                                "display_name": display_name,
                                "avatar_url": avatar_url,
                                **user_info
                            }
                        )
                        
                        if not is_new or not new_user:
                            return SocialLoginResponse(
                                success=False,
                                error_message=error_msg or "Failed to create user from social login",
                                error_code="USER_CREATION_FAILED"
                            )
                        
                        # Check if username is taken (if provided)
                        if new_user.username and await self.user_repository.username_exists(new_user.username):
                            # Generate unique username
                            base_username = new_user.username
                            counter = 1
                            while await self.user_repository.username_exists(f"{base_username}{counter}"):
                                counter += 1
                            new_user.update_profile(username=f"{base_username}{counter}")
                        
                        # Create user in repository
                        user = await self.user_repository.create_user(new_user)
                        is_new_user = True
                        
                        # Send welcome email
                        await self.auth_service.send_welcome_email(user)
                
                except ValueError as e:
                    return SocialLoginResponse(
                        success=False,
                        error_message=f"Invalid email from provider: {str(e)}",
                        error_code="INVALID_PROVIDER_EMAIL"
                    )
            
            # Check if user account is active
            if not user.is_active or user.status != UserStatus.ACTIVE:
                return SocialLoginResponse(
                    success=False,
                    error_message="User account is not active",
                    error_code="ACCOUNT_INACTIVE"
                )
            
            # Update last login information
            user.record_login_attempt(success=True, ip_address=request.ip_address)
            await self.user_repository.update_user(user)
            
            # Create authentication tokens
            access_token_expires = timedelta(minutes=30)
            refresh_token_expires = timedelta(days=7)
            
            access_token = await self.token_service.create_token(
                token_type=self.token_service.TokenType.ACCESS,
                user_id=user.id,
                expires_in=access_token_expires,
                metadata={
                    "role": user.role.value,
                    "permissions": list(user.permissions),
                    "ip_address": request.ip_address,
                    "user_agent": request.user_agent,
                    "login_method": f"social_{request.provider}"
                }
            )
            
            refresh_token = await self.token_service.create_token(
                token_type=self.token_service.TokenType.REFRESH,
                user_id=user.id,
                expires_in=refresh_token_expires,
                metadata={
                    "ip_address": request.ip_address,
                    "login_method": f"social_{request.provider}"
                }
            )
            
            # Increment rate limit counter
            await self.auth_service.increment_rate_limit(
                identifier=rate_limit_key,
                action="social_login",
                window_seconds=900
            )
            
            # Log successful social login
            await self.auth_service.log_security_event(
                user_id=user.id,
                event_type="social_login_successful",
                details={
                    "provider": request.provider,
                    "provider_id": provider_id,
                    "email": user.email.value,
                    "is_new_user": is_new_user,
                    "user_info": user_info
                },
                ip_address=request.ip_address,
                user_agent=request.user_agent
            )
            
            # Log token usage
            await self.token_service.log_token_usage(
                token=access_token,
                action="social_login",
                ip_address=request.ip_address,
                user_agent=request.user_agent,
                additional_data={
                    "provider": request.provider,
                    "is_new_user": is_new_user
                }
            )
            
            # Check if profile completion is required
            requires_profile_completion = (
                is_new_user and (
                    not user.first_name or 
                    not user.last_name or 
                    not user.username
                )
            )
            
            # Get user capabilities
            user_capabilities = self.domain_service.get_user_capabilities(user)
            
            return SocialLoginResponse(
                success=True,
                user_id=user.id,
                access_token=access_token.value,
                refresh_token=refresh_token.value,
                expires_in=int(access_token_expires.total_seconds()),
                token_type="Bearer",
                is_new_user=is_new_user,
                requires_profile_completion=requires_profile_completion,
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
                    "social_accounts": [acc["provider"] for acc in user.social_accounts],
                    "capabilities": user_capabilities
                }
            )
            
        except Exception as e:
            # Log unexpected error
            await self.auth_service.log_security_event(
                user_id=None,
                event_type="social_login_error",
                details={
                    "error": str(e),
                    "provider": request.provider
                },
                ip_address=request.ip_address,
                user_agent=request.user_agent
            )
            
            return SocialLoginResponse(
                success=False,
                error_message="Social login failed due to an internal error",
                error_code="INTERNAL_ERROR"
            )
    
    async def link_social_account(
        self,
        user_id: int,
        provider: str,
        authorization_code: Optional[str] = None,
        access_token: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Link social account to existing user.
        
        Args:
            user_id: User ID to link account to
            provider: OAuth provider name
            authorization_code: OAuth authorization code
            access_token: OAuth access token
            redirect_uri: OAuth redirect URI
            ip_address: Client IP address
            user_agent: User agent string
            
        Returns:
            Dictionary with linking result
        """
        try:
            # Get user
            user = await self.user_repository.get_user_by_id(user_id)
            if not user:
                return {
                    "success": False,
                    "error_message": "User not found",
                    "error_code": "USER_NOT_FOUND"
                }
            
            # Exchange authorization code for access token if needed
            oauth_access_token = access_token
            if authorization_code and not oauth_access_token:
                token_response = await self.auth_service.exchange_oauth_code(
                    provider=provider,
                    code=authorization_code,
                    redirect_uri=redirect_uri or ""
                )
                
                if not token_response:
                    return {
                        "success": False,
                        "error_message": "Failed to exchange authorization code",
                        "error_code": "OAUTH_TOKEN_EXCHANGE_FAILED"
                    }
                
                oauth_access_token = token_response.get("access_token")
            
            if not oauth_access_token:
                return {
                    "success": False,
                    "error_message": "No OAuth access token provided",
                    "error_code": "MISSING_OAUTH_TOKEN"
                }
            
            # Get user information from provider
            user_info = await self.auth_service.get_oauth_user_info(
                provider=provider,
                access_token=oauth_access_token
            )
            
            if not user_info:
                return {
                    "success": False,
                    "error_message": "Failed to get user information from provider",
                    "error_code": "OAUTH_USER_INFO_FAILED"
                }
            
            provider_id = str(user_info.get("id") or user_info.get("sub"))
            if not provider_id:
                return {
                    "success": False,
                    "error_message": "Provider did not return user ID",
                    "error_code": "MISSING_PROVIDER_USER_ID"
                }
            
            # Check if social account is already linked to another user
            existing_user = await self.user_repository.get_user_by_social_account(
                provider=provider,
                provider_id=provider_id
            )
            
            if existing_user and existing_user.id != user_id:
                return {
                    "success": False,
                    "error_message": "Social account is already linked to another user",
                    "error_code": "SOCIAL_ACCOUNT_ALREADY_LINKED"
                }
            
            # Link social account
            success = self.domain_service.link_social_account(
                user=user,
                provider=provider,
                provider_id=provider_id,
                profile_data=user_info
            )
            
            if not success:
                return {
                    "success": False,
                    "error_message": "Failed to link social account",
                    "error_code": "SOCIAL_ACCOUNT_LINK_FAILED"
                }
            
            # Update user in repository
            await self.user_repository.update_user(user)
            
            # Log social account linking
            await self.auth_service.log_security_event(
                user_id=user.id,
                event_type="social_account_linked",
                details={
                    "provider": provider,
                    "provider_id": provider_id,
                    "user_info": user_info
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return {
                "success": True,
                "message": f"{provider.title()} account linked successfully",
                "provider": provider,
                "linked_accounts": [acc["provider"] for acc in user.social_accounts]
            }
            
        except Exception as e:
            # Log error
            await self.auth_service.log_security_event(
                user_id=user_id,
                event_type="social_account_link_error",
                details={
                    "error": str(e),
                    "provider": provider
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return {
                "success": False,
                "error_message": "Failed to link social account due to an internal error",
                "error_code": "INTERNAL_ERROR"
            }
    
    async def unlink_social_account(
        self,
        user_id: int,
        provider: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Unlink social account from user.
        
        Args:
            user_id: User ID
            provider: OAuth provider name
            ip_address: Client IP address
            user_agent: User agent string
            
        Returns:
            Dictionary with unlinking result
        """
        try:
            # Get user
            user = await self.user_repository.get_user_by_id(user_id)
            if not user:
                return {
                    "success": False,
                    "error_message": "User not found",
                    "error_code": "USER_NOT_FOUND"
                }
            
            # Unlink social account using domain service
            success = self.domain_service.unlink_social_account(user, provider)
            
            if not success:
                return {
                    "success": False,
                    "error_message": "Cannot unlink social account. It may be the only authentication method.",
                    "error_code": "CANNOT_UNLINK_ONLY_AUTH_METHOD"
                }
            
            # Update user in repository
            await self.user_repository.update_user(user)
            
            # Log social account unlinking
            await self.auth_service.log_security_event(
                user_id=user.id,
                event_type="social_account_unlinked",
                details={"provider": provider},
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return {
                "success": True,
                "message": f"{provider.title()} account unlinked successfully",
                "provider": provider,
                "remaining_accounts": [acc["provider"] for acc in user.social_accounts]
            }
            
        except Exception as e:
            # Log error
            await self.auth_service.log_security_event(
                user_id=user_id,
                event_type="social_account_unlink_error",
                details={
                    "error": str(e),
                    "provider": provider
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return {
                "success": False,
                "error_message": "Failed to unlink social account due to an internal error",
                "error_code": "INTERNAL_ERROR"
            }

