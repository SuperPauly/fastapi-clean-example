"""
AuthToken Value Object - Domain Layer

This module contains the AuthToken value object that encapsulates authentication
token logic following Domain-Driven Design principles.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum
import json
import base64


class TokenType(Enum):
    """Authentication token types."""
    ACCESS = "access"
    REFRESH = "refresh"
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
    API_KEY = "api_key"
    SESSION = "session"
    OAUTH_STATE = "oauth_state"
    OAUTH_CODE = "oauth_code"


class TokenStatus(Enum):
    """Token status enumeration."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    USED = "used"


@dataclass(frozen=True)
class AuthToken:
    """
    AuthToken value object that encapsulates authentication token logic.
    
    This value object follows hexagonal architecture principles by:
    - Being immutable (frozen dataclass)
    - Containing token validation and security logic
    - Being framework-agnostic
    - Encapsulating token-related business rules
    """
    
    value: str
    token_type: TokenType
    user_id: Optional[int] = None
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    is_revoked: bool = False
    used_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize token with default values and validation."""
        if not self.value:
            raise ValueError("Token value cannot be empty")
        
        if not self.created_at:
            object.__setattr__(self, 'created_at', datetime.utcnow())
        
        if self.metadata is None:
            object.__setattr__(self, 'metadata', {})
        
        # Validate token format based on type
        if not self._is_valid_format():
            raise ValueError(f"Invalid token format for type {self.token_type.value}")
    
    def _is_valid_format(self) -> bool:
        """Validate token format based on type."""
        if self.token_type in [TokenType.ACCESS, TokenType.REFRESH]:
            # JWT tokens should have 3 parts separated by dots
            return len(self.value.split('.')) == 3
        elif self.token_type in [TokenType.EMAIL_VERIFICATION, TokenType.PASSWORD_RESET]:
            # Verification tokens should be URL-safe base64
            try:
                base64.urlsafe_b64decode(self.value + '==')
                return len(self.value) >= 32
            except Exception:
                return False
        elif self.token_type == TokenType.API_KEY:
            # API keys should be hex strings of sufficient length
            try:
                int(self.value, 16)
                return len(self.value) >= 32
            except ValueError:
                return False
        elif self.token_type == TokenType.SESSION:
            # Session tokens should be secure random strings
            return len(self.value) >= 32 and self.value.isalnum()
        else:
            # Generic validation for other types
            return len(self.value) >= 16
    
    def is_expired(self) -> bool:
        """
        Check if token is expired.
        
        Returns:
            bool: True if token is expired
        """
        if not self.expires_at:
            return False
        
        return datetime.utcnow() >= self.expires_at
    
    def is_valid(self) -> bool:
        """
        Check if token is valid (not expired, not revoked, not used for single-use tokens).
        
        Returns:
            bool: True if token is valid
        """
        if self.is_revoked:
            return False
        
        if self.is_expired():
            return False
        
        # Single-use tokens become invalid after use
        if self.is_single_use() and self.used_at:
            return False
        
        return True
    
    def is_single_use(self) -> bool:
        """
        Check if token is single-use type.
        
        Returns:
            bool: True if token should only be used once
        """
        single_use_types = {
            TokenType.EMAIL_VERIFICATION,
            TokenType.PASSWORD_RESET,
            TokenType.OAUTH_CODE
        }
        return self.token_type in single_use_types
    
    def get_status(self) -> TokenStatus:
        """
        Get current token status.
        
        Returns:
            TokenStatus: Current status of the token
        """
        if self.is_revoked:
            return TokenStatus.REVOKED
        
        if self.is_expired():
            return TokenStatus.EXPIRED
        
        if self.is_single_use() and self.used_at:
            return TokenStatus.USED
        
        return TokenStatus.ACTIVE
    
    def get_remaining_lifetime(self) -> Optional[timedelta]:
        """
        Get remaining lifetime of the token.
        
        Returns:
            timedelta: Remaining time until expiration, None if no expiration
        """
        if not self.expires_at:
            return None
        
        remaining = self.expires_at - datetime.utcnow()
        return remaining if remaining.total_seconds() > 0 else timedelta(0)
    
    def get_age(self) -> timedelta:
        """
        Get age of the token.
        
        Returns:
            timedelta: Time since token creation
        """
        return datetime.utcnow() - self.created_at
    
    def revoke(self) -> 'AuthToken':
        """
        Create new token instance marked as revoked.
        
        Returns:
            AuthToken: New revoked token instance
        """
        return AuthToken(
            value=self.value,
            token_type=self.token_type,
            user_id=self.user_id,
            expires_at=self.expires_at,
            created_at=self.created_at,
            metadata=self.metadata,
            is_revoked=True,
            used_at=self.used_at
        )
    
    def mark_as_used(self) -> 'AuthToken':
        """
        Create new token instance marked as used.
        
        Returns:
            AuthToken: New used token instance
        """
        return AuthToken(
            value=self.value,
            token_type=self.token_type,
            user_id=self.user_id,
            expires_at=self.expires_at,
            created_at=self.created_at,
            metadata=self.metadata,
            is_revoked=self.is_revoked,
            used_at=datetime.utcnow()
        )
    
    def add_metadata(self, key: str, value: Any) -> 'AuthToken':
        """
        Create new token instance with additional metadata.
        
        Args:
            key: Metadata key
            value: Metadata value
            
        Returns:
            AuthToken: New token instance with added metadata
        """
        new_metadata = self.metadata.copy()
        new_metadata[key] = value
        
        return AuthToken(
            value=self.value,
            token_type=self.token_type,
            user_id=self.user_id,
            expires_at=self.expires_at,
            created_at=self.created_at,
            metadata=new_metadata,
            is_revoked=self.is_revoked,
            used_at=self.used_at
        )
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata value by key.
        
        Args:
            key: Metadata key
            default: Default value if key not found
            
        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default)
    
    def get_hash(self) -> str:
        """
        Get SHA-256 hash of the token value for secure storage.
        
        Returns:
            str: Hexadecimal hash of token value
        """
        return hashlib.sha256(self.value.encode()).hexdigest()
    
    def get_masked_value(self, show_chars: int = 4) -> str:
        """
        Get masked version of token for logging/display.
        
        Args:
            show_chars: Number of characters to show at the end
            
        Returns:
            str: Masked token value
        """
        if len(self.value) <= show_chars:
            return '*' * len(self.value)
        
        return '*' * (len(self.value) - show_chars) + self.value[-show_chars:]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert token to dictionary representation.
        
        Returns:
            Dict representation of token (excluding sensitive value)
        """
        return {
            'token_type': self.token_type.value,
            'user_id': self.user_id,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'metadata': self.metadata,
            'is_revoked': self.is_revoked,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'status': self.get_status().value,
            'is_valid': self.is_valid(),
            'is_expired': self.is_expired(),
            'remaining_lifetime_seconds': (
                self.get_remaining_lifetime().total_seconds() 
                if self.get_remaining_lifetime() else None
            ),
            'age_seconds': self.get_age().total_seconds(),
            'masked_value': self.get_masked_value()
        }
    
    @classmethod
    def generate_access_token(
        cls,
        user_id: int,
        expires_in_minutes: int = 30,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'AuthToken':
        """
        Generate a new access token.
        
        Args:
            user_id: User ID for the token
            expires_in_minutes: Token expiration time in minutes
            metadata: Additional token metadata
            
        Returns:
            AuthToken: New access token
        """
        # This is a placeholder - in real implementation, use proper JWT library
        header = base64.urlsafe_b64encode(
            json.dumps({"alg": "HS256", "typ": "JWT"}).encode()
        ).decode().rstrip('=')
        
        payload = base64.urlsafe_b64encode(
            json.dumps({
                "user_id": user_id,
                "exp": int((datetime.utcnow() + timedelta(minutes=expires_in_minutes)).timestamp()),
                "iat": int(datetime.utcnow().timestamp()),
                "type": "access"
            }).encode()
        ).decode().rstrip('=')
        
        # Placeholder signature
        signature = base64.urlsafe_b64encode(
            hashlib.sha256(f"{header}.{payload}".encode()).digest()
        ).decode().rstrip('=')
        
        token_value = f"{header}.{payload}.{signature}"
        
        return cls(
            value=token_value,
            token_type=TokenType.ACCESS,
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(minutes=expires_in_minutes),
            metadata=metadata or {}
        )
    
    @classmethod
    def generate_refresh_token(
        cls,
        user_id: int,
        expires_in_days: int = 7,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'AuthToken':
        """
        Generate a new refresh token.
        
        Args:
            user_id: User ID for the token
            expires_in_days: Token expiration time in days
            metadata: Additional token metadata
            
        Returns:
            AuthToken: New refresh token
        """
        # Similar to access token but with longer expiration
        header = base64.urlsafe_b64encode(
            json.dumps({"alg": "HS256", "typ": "JWT"}).encode()
        ).decode().rstrip('=')
        
        payload = base64.urlsafe_b64encode(
            json.dumps({
                "user_id": user_id,
                "exp": int((datetime.utcnow() + timedelta(days=expires_in_days)).timestamp()),
                "iat": int(datetime.utcnow().timestamp()),
                "type": "refresh"
            }).encode()
        ).decode().rstrip('=')
        
        signature = base64.urlsafe_b64encode(
            hashlib.sha256(f"{header}.{payload}".encode()).digest()
        ).decode().rstrip('=')
        
        token_value = f"{header}.{payload}.{signature}"
        
        return cls(
            value=token_value,
            token_type=TokenType.REFRESH,
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
            metadata=metadata or {}
        )
    
    @classmethod
    def generate_verification_token(
        cls,
        user_id: int,
        token_type: TokenType,
        expires_in_hours: int = 24,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'AuthToken':
        """
        Generate a verification token (email verification, password reset, etc.).
        
        Args:
            user_id: User ID for the token
            token_type: Type of verification token
            expires_in_hours: Token expiration time in hours
            metadata: Additional token metadata
            
        Returns:
            AuthToken: New verification token
        """
        # Generate secure random token
        token_bytes = secrets.token_bytes(32)
        token_value = base64.urlsafe_b64encode(token_bytes).decode().rstrip('=')
        
        return cls(
            value=token_value,
            token_type=token_type,
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours),
            metadata=metadata or {}
        )
    
    @classmethod
    def generate_api_key(
        cls,
        user_id: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'AuthToken':
        """
        Generate a long-lived API key.
        
        Args:
            user_id: User ID for the token
            metadata: Additional token metadata
            
        Returns:
            AuthToken: New API key token
        """
        # Generate secure hex API key
        token_value = secrets.token_hex(32)
        
        return cls(
            value=token_value,
            token_type=TokenType.API_KEY,
            user_id=user_id,
            expires_at=None,  # API keys don't expire by default
            metadata=metadata or {}
        )
    
    @classmethod
    def generate_session_token(
        cls,
        user_id: int,
        expires_in_hours: int = 24,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'AuthToken':
        """
        Generate a session token.
        
        Args:
            user_id: User ID for the token
            expires_in_hours: Token expiration time in hours
            metadata: Additional token metadata
            
        Returns:
            AuthToken: New session token
        """
        # Generate secure alphanumeric session token
        token_value = ''.join(secrets.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(64))
        
        return cls(
            value=token_value,
            token_type=TokenType.SESSION,
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours),
            metadata=metadata or {}
        )
    
    def __str__(self) -> str:
        """String representation (masked for security)."""
        return f"{self.token_type.value}:{self.get_masked_value()}"
    
    def __repr__(self) -> str:
        """Detailed string representation (masked for security)."""
        return (
            f"AuthToken(type={self.token_type.value}, user_id={self.user_id}, "
            f"status={self.get_status().value}, masked_value='{self.get_masked_value()}')"
        )
    
    def __eq__(self, other) -> bool:
        """Compare tokens for equality."""
        if isinstance(other, AuthToken):
            return self.value == other.value and self.token_type == other.token_type
        return False
    
    def __hash__(self) -> int:
        """Hash function for token."""
        return hash((self.value, self.token_type))

