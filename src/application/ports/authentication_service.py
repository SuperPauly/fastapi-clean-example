"""
Authentication Service Port - Application Layer

This module defines the authentication service port (interface) following
hexagonal architecture principles.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from ...domain.entities.user import User
from ...domain.value_objects.auth_token import AuthToken, TokenType
from ...domain.value_objects.password import Password


class AuthenticationServicePort(ABC):
    """
    Authentication service port defining the interface for authentication operations.
    
    This port follows hexagonal architecture principles by:
    - Defining the interface without implementation details
    - Being framework-agnostic
    - Allowing dependency inversion
    - Enabling testability through mocking
    """
    
    @abstractmethod
    async def hash_password(self, password: str) -> str:
        """
        Hash a password using secure algorithm.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        pass
    
    @abstractmethod
    async def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plain text password
            hashed_password: Hashed password to verify against
            
        Returns:
            bool: True if password matches
        """
        pass
    
    @abstractmethod
    async def generate_jwt_token(
        self,
        payload: Dict[str, Any],
        expires_in_minutes: int = 30,
        token_type: str = "access"
    ) -> str:
        """
        Generate JWT token with payload.
        
        Args:
            payload: Token payload data
            expires_in_minutes: Token expiration time
            token_type: Type of token (access, refresh)
            
        Returns:
            JWT token string
        """
        pass
    
    @abstractmethod
    async def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload or None if invalid
        """
        pass
    
    @abstractmethod
    async def generate_secure_token(self, length: int = 32) -> str:
        """
        Generate cryptographically secure random token.
        
        Args:
            length: Token length in bytes
            
        Returns:
            Secure token string
        """
        pass
    
    @abstractmethod
    async def generate_verification_token(
        self,
        user_id: int,
        token_type: TokenType,
        expires_in_hours: int = 24
    ) -> AuthToken:
        """
        Generate verification token for email/password reset.
        
        Args:
            user_id: User ID
            token_type: Type of verification token
            expires_in_hours: Token expiration time
            
        Returns:
            AuthToken instance
        """
        pass
    
    @abstractmethod
    async def send_verification_email(
        self,
        user: User,
        verification_token: AuthToken
    ) -> bool:
        """
        Send email verification email to user.
        
        Args:
            user: User entity
            verification_token: Email verification token
            
        Returns:
            bool: True if email sent successfully
        """
        pass
    
    @abstractmethod
    async def send_password_reset_email(
        self,
        user: User,
        reset_token: AuthToken
    ) -> bool:
        """
        Send password reset email to user.
        
        Args:
            user: User entity
            reset_token: Password reset token
            
        Returns:
            bool: True if email sent successfully
        """
        pass
    
    @abstractmethod
    async def send_welcome_email(self, user: User) -> bool:
        """
        Send welcome email to new user.
        
        Args:
            user: User entity
            
        Returns:
            bool: True if email sent successfully
        """
        pass
    
    @abstractmethod
    async def send_login_notification(
        self,
        user: User,
        ip_address: str,
        user_agent: str
    ) -> bool:
        """
        Send login notification email.
        
        Args:
            user: User entity
            ip_address: Login IP address
            user_agent: User agent string
            
        Returns:
            bool: True if email sent successfully
        """
        pass
    
    @abstractmethod
    async def validate_oauth_state(self, state: str) -> bool:
        """
        Validate OAuth state parameter.
        
        Args:
            state: OAuth state parameter
            
        Returns:
            bool: True if state is valid
        """
        pass
    
    @abstractmethod
    async def generate_oauth_state(self) -> str:
        """
        Generate OAuth state parameter.
        
        Returns:
            OAuth state string
        """
        pass
    
    @abstractmethod
    async def get_oauth_authorization_url(
        self,
        provider: str,
        redirect_uri: str,
        state: str,
        scopes: Optional[List[str]] = None
    ) -> str:
        """
        Get OAuth authorization URL for provider.
        
        Args:
            provider: OAuth provider name
            redirect_uri: Redirect URI after authorization
            state: OAuth state parameter
            scopes: Optional list of scopes to request
            
        Returns:
            Authorization URL
        """
        pass
    
    @abstractmethod
    async def exchange_oauth_code(
        self,
        provider: str,
        code: str,
        redirect_uri: str
    ) -> Optional[Dict[str, Any]]:
        """
        Exchange OAuth authorization code for access token.
        
        Args:
            provider: OAuth provider name
            code: Authorization code
            redirect_uri: Redirect URI used in authorization
            
        Returns:
            Token response data or None if exchange failed
        """
        pass
    
    @abstractmethod
    async def get_oauth_user_info(
        self,
        provider: str,
        access_token: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get user information from OAuth provider.
        
        Args:
            provider: OAuth provider name
            access_token: OAuth access token
            
        Returns:
            User information or None if request failed
        """
        pass
    
    @abstractmethod
    async def validate_recaptcha(self, recaptcha_response: str) -> bool:
        """
        Validate reCAPTCHA response.
        
        Args:
            recaptcha_response: reCAPTCHA response token
            
        Returns:
            bool: True if reCAPTCHA is valid
        """
        pass
    
    @abstractmethod
    async def check_password_breach(self, password: str) -> bool:
        """
        Check if password has been breached using HaveIBeenPwned API.
        
        Args:
            password: Password to check
            
        Returns:
            bool: True if password has been breached
        """
        pass
    
    @abstractmethod
    async def generate_totp_secret(self) -> str:
        """
        Generate TOTP secret for 2FA.
        
        Returns:
            Base32-encoded TOTP secret
        """
        pass
    
    @abstractmethod
    async def verify_totp_code(self, secret: str, code: str) -> bool:
        """
        Verify TOTP code for 2FA.
        
        Args:
            secret: TOTP secret
            code: TOTP code to verify
            
        Returns:
            bool: True if code is valid
        """
        pass
    
    @abstractmethod
    async def generate_backup_codes(self, count: int = 10) -> List[str]:
        """
        Generate backup codes for 2FA.
        
        Args:
            count: Number of backup codes to generate
            
        Returns:
            List of backup codes
        """
        pass
    
    @abstractmethod
    async def log_security_event(
        self,
        user_id: Optional[int],
        event_type: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Log security-related event.
        
        Args:
            user_id: User ID (if applicable)
            event_type: Type of security event
            details: Event details
            ip_address: Client IP address
            user_agent: User agent string
        """
        pass
    
    @abstractmethod
    async def get_security_events(
        self,
        user_id: Optional[int] = None,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get security events with filtering.
        
        Args:
            user_id: Filter by user ID
            event_type: Filter by event type
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of events to return
            
        Returns:
            List of security events
        """
        pass
    
    @abstractmethod
    async def detect_suspicious_activity(
        self,
        user_id: int,
        ip_address: str,
        user_agent: str
    ) -> Dict[str, Any]:
        """
        Detect suspicious login activity.
        
        Args:
            user_id: User ID
            ip_address: Login IP address
            user_agent: User agent string
            
        Returns:
            Dictionary with suspicion analysis results
        """
        pass
    
    @abstractmethod
    async def get_geolocation(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """
        Get geolocation information for IP address.
        
        Args:
            ip_address: IP address to lookup
            
        Returns:
            Geolocation data or None if lookup failed
        """
        pass
    
    @abstractmethod
    async def check_rate_limit(
        self,
        identifier: str,
        action: str,
        limit: int,
        window_seconds: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if action is rate limited.
        
        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            action: Action being performed
            limit: Maximum number of actions allowed
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        pass
    
    @abstractmethod
    async def increment_rate_limit(
        self,
        identifier: str,
        action: str,
        window_seconds: int
    ) -> None:
        """
        Increment rate limit counter.
        
        Args:
            identifier: Unique identifier
            action: Action being performed
            window_seconds: Time window in seconds
        """
        pass


class AuthenticationServiceError(Exception):
    """Base exception for authentication service errors."""
    pass


class TokenGenerationError(AuthenticationServiceError):
    """Exception raised when token generation fails."""
    pass


class TokenVerificationError(AuthenticationServiceError):
    """Exception raised when token verification fails."""
    pass


class EmailDeliveryError(AuthenticationServiceError):
    """Exception raised when email delivery fails."""
    pass


class OAuthError(AuthenticationServiceError):
    """Exception raised during OAuth operations."""
    pass


class RateLimitExceededError(AuthenticationServiceError):
    """Exception raised when rate limit is exceeded."""
    pass

