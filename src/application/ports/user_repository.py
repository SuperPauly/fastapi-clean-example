"""
User Repository Port - Application Layer

This module defines the user repository port (interface) following
hexagonal architecture principles.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime

from ...domain.entities.user import User
from ...domain.value_objects.email import Email
from ...domain.value_objects.auth_token import AuthToken


class UserRepositoryPort(ABC):
    """
    User repository port defining the interface for user data persistence.
    
    This port follows hexagonal architecture principles by:
    - Defining the interface without implementation details
    - Being framework-agnostic
    - Allowing dependency inversion
    - Enabling testability through mocking
    """
    
    @abstractmethod
    async def create_user(self, user: User) -> User:
        """
        Create a new user in the repository.
        
        Args:
            user: User entity to create
            
        Returns:
            User: Created user with assigned ID
            
        Raises:
            UserAlreadyExistsError: If user with email already exists
            RepositoryError: If creation fails
        """
        pass
    
    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID to search for
            
        Returns:
            User entity or None if not found
        """
        pass
    
    @abstractmethod
    async def get_user_by_email(self, email: Email) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: Email value object to search for
            
        Returns:
            User entity or None if not found
        """
        pass
    
    @abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User entity or None if not found
        """
        pass
    
    @abstractmethod
    async def get_user_by_social_account(
        self, 
        provider: str, 
        provider_id: str
    ) -> Optional[User]:
        """
        Get user by social account provider and ID.
        
        Args:
            provider: OAuth provider name
            provider_id: Provider-specific user ID
            
        Returns:
            User entity or None if not found
        """
        pass
    
    @abstractmethod
    async def update_user(self, user: User) -> User:
        """
        Update existing user in the repository.
        
        Args:
            user: User entity with updated data
            
        Returns:
            Updated user entity
            
        Raises:
            UserNotFoundError: If user doesn't exist
            RepositoryError: If update fails
        """
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: int) -> bool:
        """
        Delete user from the repository.
        
        Args:
            user_id: ID of user to delete
            
        Returns:
            bool: True if deletion successful
            
        Raises:
            UserNotFoundError: If user doesn't exist
            RepositoryError: If deletion fails
        """
        pass
    
    @abstractmethod
    async def list_users(
        self,
        offset: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[User]:
        """
        List users with pagination and filtering.
        
        Args:
            offset: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional filters to apply
            sort_by: Field to sort by
            sort_order: Sort order ("asc" or "desc")
            
        Returns:
            List of user entities
        """
        pass
    
    @abstractmethod
    async def count_users(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count users matching filters.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Number of matching users
        """
        pass
    
    @abstractmethod
    async def search_users(
        self,
        query: str,
        offset: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        Search users by query string.
        
        Args:
            query: Search query
            offset: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching user entities
        """
        pass
    
    @abstractmethod
    async def get_users_by_role(self, role: str) -> List[User]:
        """
        Get all users with specific role.
        
        Args:
            role: Role name to filter by
            
        Returns:
            List of users with the specified role
        """
        pass
    
    @abstractmethod
    async def get_users_by_status(self, status: str) -> List[User]:
        """
        Get all users with specific status.
        
        Args:
            status: User status to filter by
            
        Returns:
            List of users with the specified status
        """
        pass
    
    @abstractmethod
    async def get_users_created_between(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[User]:
        """
        Get users created between specified dates.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            List of users created in the date range
        """
        pass
    
    @abstractmethod
    async def get_users_last_login_before(self, date: datetime) -> List[User]:
        """
        Get users who haven't logged in since specified date.
        
        Args:
            date: Date threshold
            
        Returns:
            List of users with last login before the date
        """
        pass
    
    @abstractmethod
    async def email_exists(self, email: Email) -> bool:
        """
        Check if email already exists in the repository.
        
        Args:
            email: Email value object to check
            
        Returns:
            bool: True if email exists
        """
        pass
    
    @abstractmethod
    async def username_exists(self, username: str) -> bool:
        """
        Check if username already exists in the repository.
        
        Args:
            username: Username to check
            
        Returns:
            bool: True if username exists
        """
        pass
    
    @abstractmethod
    async def store_token(self, token: AuthToken) -> bool:
        """
        Store authentication token in the repository.
        
        Args:
            token: AuthToken to store
            
        Returns:
            bool: True if storage successful
        """
        pass
    
    @abstractmethod
    async def get_token(self, token_value: str) -> Optional[AuthToken]:
        """
        Get authentication token by value.
        
        Args:
            token_value: Token value to search for
            
        Returns:
            AuthToken or None if not found
        """
        pass
    
    @abstractmethod
    async def get_user_tokens(
        self,
        user_id: int,
        token_type: Optional[str] = None,
        active_only: bool = True
    ) -> List[AuthToken]:
        """
        Get all tokens for a user.
        
        Args:
            user_id: User ID
            token_type: Optional token type filter
            active_only: Whether to return only active tokens
            
        Returns:
            List of user's tokens
        """
        pass
    
    @abstractmethod
    async def revoke_token(self, token_value: str) -> bool:
        """
        Revoke authentication token.
        
        Args:
            token_value: Token value to revoke
            
        Returns:
            bool: True if revocation successful
        """
        pass
    
    @abstractmethod
    async def revoke_user_tokens(
        self,
        user_id: int,
        token_type: Optional[str] = None
    ) -> int:
        """
        Revoke all tokens for a user.
        
        Args:
            user_id: User ID
            token_type: Optional token type filter
            
        Returns:
            Number of tokens revoked
        """
        pass
    
    @abstractmethod
    async def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired tokens from the repository.
        
        Returns:
            Number of tokens cleaned up
        """
        pass
    
    @abstractmethod
    async def get_user_statistics(self) -> Dict[str, Any]:
        """
        Get user statistics.
        
        Returns:
            Dictionary containing user statistics
        """
        pass
    
    @abstractmethod
    async def get_login_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get login statistics for specified date range.
        
        Args:
            start_date: Start date for statistics
            end_date: End date for statistics
            
        Returns:
            Dictionary containing login statistics
        """
        pass
    
    @abstractmethod
    async def begin_transaction(self):
        """Begin a database transaction."""
        pass
    
    @abstractmethod
    async def commit_transaction(self):
        """Commit the current transaction."""
        pass
    
    @abstractmethod
    async def rollback_transaction(self):
        """Rollback the current transaction."""
        pass


class UserRepositoryError(Exception):
    """Base exception for user repository errors."""
    pass


class UserNotFoundError(UserRepositoryError):
    """Exception raised when user is not found."""
    pass


class UserAlreadyExistsError(UserRepositoryError):
    """Exception raised when user already exists."""
    pass


class TokenNotFoundError(UserRepositoryError):
    """Exception raised when token is not found."""
    pass


class TokenExpiredError(UserRepositoryError):
    """Exception raised when token is expired."""
    pass

