"""
Token Service Port - Application Layer

This module defines the token service port (interface) following
hexagonal architecture principles.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from ...domain.value_objects.auth_token import AuthToken, TokenType


class TokenServicePort(ABC):
    """
    Token service port defining the interface for token management operations.
    
    This port follows hexagonal architecture principles by:
    - Defining the interface without implementation details
    - Being framework-agnostic
    - Allowing dependency inversion
    - Enabling testability through mocking
    """
    
    @abstractmethod
    async def create_token(
        self,
        token_type: TokenType,
        user_id: int,
        expires_in: Optional[timedelta] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuthToken:
        """
        Create a new authentication token.
        
        Args:
            token_type: Type of token to create
            user_id: User ID the token belongs to
            expires_in: Token expiration duration
            metadata: Additional token metadata
            
        Returns:
            AuthToken: Created token
        """
        pass
    
    @abstractmethod
    async def validate_token(
        self,
        token_value: str,
        expected_type: Optional[TokenType] = None
    ) -> Optional[AuthToken]:
        """
        Validate and retrieve token information.
        
        Args:
            token_value: Token value to validate
            expected_type: Expected token type for validation
            
        Returns:
            AuthToken if valid, None if invalid
        """
        pass
    
    @abstractmethod
    async def refresh_token(
        self,
        refresh_token: AuthToken,
        new_expires_in: Optional[timedelta] = None
    ) -> Optional[AuthToken]:
        """
        Create new access token from refresh token.
        
        Args:
            refresh_token: Valid refresh token
            new_expires_in: Expiration duration for new token
            
        Returns:
            New access token or None if refresh failed
        """
        pass
    
    @abstractmethod
    async def revoke_token(self, token_value: str) -> bool:
        """
        Revoke a specific token.
        
        Args:
            token_value: Token value to revoke
            
        Returns:
            bool: True if revocation successful
        """
        pass
    
    @abstractmethod
    async def revoke_all_user_tokens(
        self,
        user_id: int,
        token_type: Optional[TokenType] = None,
        exclude_token: Optional[str] = None
    ) -> int:
        """
        Revoke all tokens for a user.
        
        Args:
            user_id: User ID
            token_type: Optional token type filter
            exclude_token: Optional token to exclude from revocation
            
        Returns:
            Number of tokens revoked
        """
        pass
    
    @abstractmethod
    async def get_user_tokens(
        self,
        user_id: int,
        token_type: Optional[TokenType] = None,
        active_only: bool = True
    ) -> List[AuthToken]:
        """
        Get all tokens for a user.
        
        Args:
            user_id: User ID
            token_type: Optional token type filter
            active_only: Whether to return only active tokens
            
        Returns:
            List of user tokens
        """
        pass
    
    @abstractmethod
    async def cleanup_expired_tokens(self) -> int:
        """
        Remove expired tokens from storage.
        
        Returns:
            Number of tokens cleaned up
        """
        pass
    
    @abstractmethod
    async def get_token_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get token usage statistics.
        
        Args:
            start_date: Start date for statistics
            end_date: End date for statistics
            
        Returns:
            Dictionary containing token statistics
        """
        pass
    
    @abstractmethod
    async def is_token_blacklisted(self, token_value: str) -> bool:
        """
        Check if token is blacklisted.
        
        Args:
            token_value: Token value to check
            
        Returns:
            bool: True if token is blacklisted
        """
        pass
    
    @abstractmethod
    async def blacklist_token(
        self,
        token_value: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Add token to blacklist.
        
        Args:
            token_value: Token value to blacklist
            reason: Optional reason for blacklisting
            
        Returns:
            bool: True if blacklisting successful
        """
        pass
    
    @abstractmethod
    async def remove_from_blacklist(self, token_value: str) -> bool:
        """
        Remove token from blacklist.
        
        Args:
            token_value: Token value to remove from blacklist
            
        Returns:
            bool: True if removal successful
        """
        pass
    
    @abstractmethod
    async def decode_jwt_payload(self, token_value: str) -> Optional[Dict[str, Any]]:
        """
        Decode JWT token payload without validation.
        
        Args:
            token_value: JWT token value
            
        Returns:
            Decoded payload or None if not a valid JWT
        """
        pass
    
    @abstractmethod
    async def verify_jwt_signature(self, token_value: str) -> bool:
        """
        Verify JWT token signature.
        
        Args:
            token_value: JWT token value
            
        Returns:
            bool: True if signature is valid
        """
        pass
    
    @abstractmethod
    async def get_token_claims(self, token: AuthToken) -> Dict[str, Any]:
        """
        Get token claims/payload.
        
        Args:
            token: AuthToken instance
            
        Returns:
            Dictionary of token claims
        """
        pass
    
    @abstractmethod
    async def create_session_token(
        self,
        user_id: int,
        session_data: Dict[str, Any],
        expires_in_hours: int = 24
    ) -> AuthToken:
        """
        Create session token with session data.
        
        Args:
            user_id: User ID
            session_data: Session data to store
            expires_in_hours: Session expiration in hours
            
        Returns:
            Session token
        """
        pass
    
    @abstractmethod
    async def get_session_data(self, session_token: AuthToken) -> Optional[Dict[str, Any]]:
        """
        Get session data from session token.
        
        Args:
            session_token: Session token
            
        Returns:
            Session data or None if invalid
        """
        pass
    
    @abstractmethod
    async def update_session_data(
        self,
        session_token: AuthToken,
        session_data: Dict[str, Any]
    ) -> bool:
        """
        Update session data for session token.
        
        Args:
            session_token: Session token
            session_data: Updated session data
            
        Returns:
            bool: True if update successful
        """
        pass
    
    @abstractmethod
    async def extend_token_expiration(
        self,
        token_value: str,
        extend_by: timedelta
    ) -> bool:
        """
        Extend token expiration time.
        
        Args:
            token_value: Token value
            extend_by: Duration to extend by
            
        Returns:
            bool: True if extension successful
        """
        pass
    
    @abstractmethod
    async def get_token_usage_history(
        self,
        token_value: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get token usage history.
        
        Args:
            token_value: Token value
            limit: Maximum number of usage records
            
        Returns:
            List of token usage records
        """
        pass
    
    @abstractmethod
    async def log_token_usage(
        self,
        token: AuthToken,
        action: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log token usage event.
        
        Args:
            token: AuthToken instance
            action: Action performed with token
            ip_address: Client IP address
            user_agent: User agent string
            additional_data: Additional usage data
        """
        pass
    
    @abstractmethod
    async def create_api_key(
        self,
        user_id: int,
        name: str,
        permissions: List[str],
        expires_in: Optional[timedelta] = None
    ) -> AuthToken:
        """
        Create API key token.
        
        Args:
            user_id: User ID
            name: API key name/description
            permissions: List of permissions for the API key
            expires_in: Optional expiration duration
            
        Returns:
            API key token
        """
        pass
    
    @abstractmethod
    async def validate_api_key_permissions(
        self,
        api_key: AuthToken,
        required_permission: str
    ) -> bool:
        """
        Validate API key has required permission.
        
        Args:
            api_key: API key token
            required_permission: Permission to check
            
        Returns:
            bool: True if API key has permission
        """
        pass
    
    @abstractmethod
    async def rotate_api_key(self, old_api_key: AuthToken) -> AuthToken:
        """
        Rotate API key (create new one with same permissions).
        
        Args:
            old_api_key: Existing API key to rotate
            
        Returns:
            New API key token
        """
        pass
    
    @abstractmethod
    async def get_token_fingerprint(self, token_value: str) -> str:
        """
        Get unique fingerprint for token.
        
        Args:
            token_value: Token value
            
        Returns:
            Token fingerprint (hash)
        """
        pass
    
    @abstractmethod
    async def verify_token_integrity(self, token: AuthToken) -> bool:
        """
        Verify token integrity and authenticity.
        
        Args:
            token: AuthToken to verify
            
        Returns:
            bool: True if token is authentic and unmodified
        """
        pass


class TokenServiceError(Exception):
    """Base exception for token service errors."""
    pass


class InvalidTokenError(TokenServiceError):
    """Exception raised when token is invalid."""
    pass


class ExpiredTokenError(TokenServiceError):
    """Exception raised when token is expired."""
    pass


class RevokedTokenError(TokenServiceError):
    """Exception raised when token is revoked."""
    pass


class TokenCreationError(TokenServiceError):
    """Exception raised when token creation fails."""
    pass


class TokenStorageError(TokenServiceError):
    """Exception raised when token storage fails."""
    pass

