"""
Authentication Domain Service - Domain Layer

This module contains the authentication domain service that encapsulates
authentication business logic following Domain-Driven Design principles.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

from ..entities.user import User, UserStatus
from ..value_objects.email import Email
from ..value_objects.password import Password, PasswordPolicy
from ..value_objects.user_role import UserRole
from ..value_objects.auth_token import AuthToken, TokenType


@dataclass
class AuthenticationResult:
    """Result of authentication attempt."""
    success: bool
    user: Optional[User] = None
    tokens: Optional[Dict[str, AuthToken]] = None
    error_message: Optional[str] = None
    requires_verification: bool = False
    account_locked: bool = False
    lockout_expires_at: Optional[datetime] = None


@dataclass
class RegistrationResult:
    """Result of user registration attempt."""
    success: bool
    user: Optional[User] = None
    verification_token: Optional[AuthToken] = None
    error_message: Optional[str] = None


class AuthenticationDomainService:
    """
    Authentication domain service that encapsulates authentication business logic.
    
    This service follows hexagonal architecture principles by:
    - Containing pure business logic
    - Being framework-agnostic
    - Using domain entities and value objects
    - Not depending on external infrastructure
    """
    
    def __init__(self, password_policy: Optional[PasswordPolicy] = None):
        """
        Initialize authentication service.
        
        Args:
            password_policy: Password policy to enforce
        """
        self.password_policy = password_policy or PasswordPolicy()
    
    def register_user(
        self,
        email: str,
        password: str,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        role: str = "user",
        require_verification: bool = True
    ) -> RegistrationResult:
        """
        Register a new user with validation.
        
        Args:
            email: User email address
            password: User password
            username: Optional username
            first_name: Optional first name
            last_name: Optional last name
            role: User role (default: "user")
            require_verification: Whether email verification is required
            
        Returns:
            RegistrationResult: Result of registration attempt
        """
        try:
            # Validate and create email value object
            user_email = Email(email)
            
            # Check for disposable email
            if user_email.is_disposable_email():
                return RegistrationResult(
                    success=False,
                    error_message="Disposable email addresses are not allowed"
                )
            
            # Validate and create password value object
            user_password = Password.create_from_raw(password, self.password_policy)
            
            # Create user role
            user_role = UserRole(role)
            
            # Create user entity
            user = User(
                email=user_email,
                password=user_password,
                username=username,
                first_name=first_name,
                last_name=last_name,
                role=user_role,
                is_verified=not require_verification,
                status=UserStatus.ACTIVE if not require_verification else UserStatus.PENDING_VERIFICATION
            )
            
            # Generate verification token if required
            verification_token = None
            if require_verification:
                verification_token = AuthToken.generate_verification_token(
                    user_id=user.id,  # Will be set by repository
                    token_type=TokenType.EMAIL_VERIFICATION,
                    expires_in_hours=24,
                    metadata={'email': user_email.value}
                )
            
            return RegistrationResult(
                success=True,
                user=user,
                verification_token=verification_token
            )
            
        except ValueError as e:
            return RegistrationResult(
                success=False,
                error_message=str(e)
            )
    
    def authenticate_user(
        self,
        user: User,
        password: str,
        ip_address: Optional[str] = None,
        max_login_attempts: int = 5,
        lockout_duration_minutes: int = 30
    ) -> AuthenticationResult:
        """
        Authenticate user with password.
        
        Args:
            user: User entity to authenticate
            password: Password to verify
            ip_address: Client IP address
            max_login_attempts: Maximum failed login attempts before lockout
            lockout_duration_minutes: Account lockout duration in minutes
            
        Returns:
            AuthenticationResult: Result of authentication attempt
        """
        # Check if account is locked
        if user.is_locked():
            return AuthenticationResult(
                success=False,
                error_message="Account is temporarily locked due to too many failed login attempts",
                account_locked=True,
                lockout_expires_at=user.locked_until
            )
        
        # Check if account is active
        if not user.is_active:
            return AuthenticationResult(
                success=False,
                error_message="Account is not active"
            )
        
        # Check if account is suspended
        if user.status == UserStatus.SUSPENDED:
            return AuthenticationResult(
                success=False,
                error_message="Account has been suspended"
            )
        
        # Verify password
        if not user.password or not user.password.verify_password(password):
            # Record failed login attempt
            user.record_login_attempt(success=False, ip_address=ip_address)
            
            # Check if account should be locked
            if user.should_lock_account(max_login_attempts):
                user.lock_account(lockout_duration_minutes)
                return AuthenticationResult(
                    success=False,
                    error_message="Too many failed login attempts. Account has been temporarily locked.",
                    account_locked=True,
                    lockout_expires_at=user.locked_until
                )
            
            remaining_attempts = max_login_attempts - user.failed_login_attempts
            return AuthenticationResult(
                success=False,
                error_message=f"Invalid password. {remaining_attempts} attempts remaining."
            )
        
        # Check if email verification is required
        if not user.is_verified and user.status == UserStatus.PENDING_VERIFICATION:
            return AuthenticationResult(
                success=False,
                error_message="Email verification required",
                requires_verification=True
            )
        
        # Successful authentication
        user.record_login_attempt(success=True, ip_address=ip_address)
        
        # Generate tokens
        access_token = AuthToken.generate_access_token(
            user_id=user.id,
            expires_in_minutes=30,
            metadata={
                'role': user.role.value,
                'permissions': list(user.permissions),
                'ip_address': ip_address
            }
        )
        
        refresh_token = AuthToken.generate_refresh_token(
            user_id=user.id,
            expires_in_days=7,
            metadata={
                'ip_address': ip_address
            }
        )
        
        return AuthenticationResult(
            success=True,
            user=user,
            tokens={
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        )
    
    def verify_email(self, user: User, verification_token: AuthToken) -> bool:
        """
        Verify user email with verification token.
        
        Args:
            user: User entity to verify
            verification_token: Email verification token
            
        Returns:
            bool: True if verification successful
        """
        # Validate token
        if not verification_token.is_valid():
            return False
        
        if verification_token.token_type != TokenType.EMAIL_VERIFICATION:
            return False
        
        if verification_token.user_id != user.id:
            return False
        
        # Verify email
        user.verify_email()
        
        return True
    
    def initiate_password_reset(self, user: User) -> AuthToken:
        """
        Initiate password reset process.
        
        Args:
            user: User entity requesting password reset
            
        Returns:
            AuthToken: Password reset token
        """
        return AuthToken.generate_verification_token(
            user_id=user.id,
            token_type=TokenType.PASSWORD_RESET,
            expires_in_hours=2,
            metadata={'email': user.email.value}
        )
    
    def reset_password(
        self,
        user: User,
        reset_token: AuthToken,
        new_password: str
    ) -> bool:
        """
        Reset user password with reset token.
        
        Args:
            user: User entity
            reset_token: Password reset token
            new_password: New password
            
        Returns:
            bool: True if reset successful
        """
        # Validate token
        if not reset_token.is_valid():
            return False
        
        if reset_token.token_type != TokenType.PASSWORD_RESET:
            return False
        
        if reset_token.user_id != user.id:
            return False
        
        try:
            # Create new password
            new_password_obj = Password.create_from_raw(new_password, self.password_policy)
            
            # Change password
            user.change_password(new_password_obj)
            
            # Reset failed login attempts
            user.failed_login_attempts = 0
            user.unlock_account()
            
            return True
            
        except ValueError:
            return False
    
    def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Change user password.
        
        Args:
            user: User entity
            current_password: Current password for verification
            new_password: New password
            
        Returns:
            Tuple of (success, error_message)
        """
        # Verify current password
        if not user.password or not user.password.verify_password(current_password):
            return False, "Current password is incorrect"
        
        try:
            # Create new password
            new_password_obj = Password.create_from_raw(new_password, self.password_policy)
            
            # Change password
            user.change_password(new_password_obj)
            
            return True, None
            
        except ValueError as e:
            return False, str(e)
    
    def refresh_access_token(
        self,
        refresh_token: AuthToken,
        user: User
    ) -> Optional[AuthToken]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            user: User entity
            
        Returns:
            New access token or None if refresh failed
        """
        # Validate refresh token
        if not refresh_token.is_valid():
            return None
        
        if refresh_token.token_type != TokenType.REFRESH:
            return None
        
        if refresh_token.user_id != user.id:
            return None
        
        # Check if user is still active
        if not user.is_active or user.status != UserStatus.ACTIVE:
            return None
        
        # Generate new access token
        return AuthToken.generate_access_token(
            user_id=user.id,
            expires_in_minutes=30,
            metadata={
                'role': user.role.value,
                'permissions': list(user.permissions),
                'refreshed_from': refresh_token.get_hash()
            }
        )
    
    def validate_social_login(
        self,
        provider: str,
        provider_id: str,
        email: str,
        profile_data: Dict
    ) -> Tuple[bool, Optional[User], Optional[str]]:
        """
        Validate social login data and create/update user.
        
        Args:
            provider: OAuth provider name
            provider_id: Provider-specific user ID
            email: User email from provider
            profile_data: Additional profile data from provider
            
        Returns:
            Tuple of (is_new_user, user_entity, error_message)
        """
        try:
            # Validate email
            user_email = Email(email)
            
            # Create user for social login
            user = User(
                email=user_email,
                username=profile_data.get('username'),
                first_name=profile_data.get('first_name'),
                last_name=profile_data.get('last_name'),
                avatar_url=profile_data.get('avatar_url'),
                is_verified=True,  # Social logins are pre-verified
                status=UserStatus.ACTIVE,
                role=UserRole("user")
            )
            
            # Add social account
            user.add_social_account(provider, provider_id, profile_data)
            
            return True, user, None
            
        except ValueError as e:
            return False, None, str(e)
    
    def link_social_account(
        self,
        user: User,
        provider: str,
        provider_id: str,
        profile_data: Dict
    ) -> bool:
        """
        Link social account to existing user.
        
        Args:
            user: Existing user entity
            provider: OAuth provider name
            provider_id: Provider-specific user ID
            profile_data: Profile data from provider
            
        Returns:
            bool: True if linking successful
        """
        # Check if social account already exists for this provider
        existing_account = user.get_social_account(provider)
        if existing_account and existing_account['provider_id'] != provider_id:
            return False  # Different account for same provider
        
        # Add or update social account
        user.add_social_account(provider, provider_id, profile_data)
        
        return True
    
    def unlink_social_account(self, user: User, provider: str) -> bool:
        """
        Unlink social account from user.
        
        Args:
            user: User entity
            provider: OAuth provider name
            
        Returns:
            bool: True if unlinking successful
        """
        # Don't allow unlinking if it's the only authentication method
        if not user.password and len(user.social_accounts) <= 1:
            return False
        
        return user.remove_social_account(provider)
    
    def generate_api_key(self, user: User, name: str = "API Key") -> AuthToken:
        """
        Generate API key for user.
        
        Args:
            user: User entity
            name: API key name/description
            
        Returns:
            AuthToken: Generated API key
        """
        return AuthToken.generate_api_key(
            user_id=user.id,
            metadata={
                'name': name,
                'created_by': user.id,
                'permissions': list(user.permissions)
            }
        )
    
    def validate_permission(
        self,
        user: User,
        required_permission: str,
        resource_id: Optional[str] = None
    ) -> bool:
        """
        Validate if user has required permission.
        
        Args:
            user: User entity
            required_permission: Permission to check
            resource_id: Optional resource ID for resource-specific permissions
            
        Returns:
            bool: True if user has permission
        """
        # Check if user is active
        if not user.is_active or user.status != UserStatus.ACTIVE:
            return False
        
        # Check permission
        if user.has_permission(required_permission):
            return True
        
        # Check resource-specific permissions if resource_id provided
        if resource_id:
            resource_permission = f"{required_permission}:{resource_id}"
            return user.has_permission(resource_permission)
        
        return False
    
    def validate_role_access(
        self,
        user: User,
        required_role: str,
        required_permissions: Optional[List[str]] = None
    ) -> bool:
        """
        Validate if user can access resource requiring specific role.
        
        Args:
            user: User entity
            required_role: Required role for access
            required_permissions: Optional additional permissions required
            
        Returns:
            bool: True if user can access resource
        """
        # Check if user is active
        if not user.is_active or user.status != UserStatus.ACTIVE:
            return False
        
        return user.can_access_resource(required_role, required_permissions)
    
    def get_user_capabilities(self, user: User) -> Dict:
        """
        Get comprehensive user capabilities and permissions.
        
        Args:
            user: User entity
            
        Returns:
            Dict: User capabilities information
        """
        return {
            'user_id': user.id,
            'role': user.role.to_dict(),
            'permissions': list(user.permissions),
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'status': user.status.value,
            'can_manage_roles': user.role.get_manageable_roles([
                'user', 'moderator', 'admin', 'superuser'
            ]),
            'accessible_resources': user.role.get_accessible_resources(),
            'social_accounts': [acc['provider'] for acc in user.social_accounts],
            'account_age_days': (datetime.utcnow() - user.created_at).days if user.created_at else 0,
            'last_login': user.last_login_at.isoformat() if user.last_login_at else None
        }

