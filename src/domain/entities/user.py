"""
User Entity - Domain Layer

This module contains the User entity following Domain-Driven Design principles.
The User entity encapsulates user business logic and maintains data integrity
while remaining framework-agnostic.
"""

from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum

from ..value_objects.email import Email
from ..value_objects.password import Password
from ..value_objects.user_role import UserRole
from ..value_objects.auth_token import AuthToken


class UserStatus(Enum):
    """User account status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    LOCKED = "locked"


@dataclass
class User:
    """
    User entity representing a user in the system.
    
    This entity follows hexagonal architecture principles by:
    - Being framework-agnostic
    - Containing business logic
    - Using value objects for data validation
    - Maintaining data integrity through domain rules
    """
    
    # Identity
    id: Optional[int] = None
    email: Email = field(default_factory=lambda: Email(""))
    username: Optional[str] = None
    
    # Authentication
    password: Optional[Password] = None
    is_verified: bool = False
    is_active: bool = True
    status: UserStatus = UserStatus.PENDING_VERIFICATION
    
    # Profile information
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    
    # Role-based access control
    role: UserRole = field(default_factory=lambda: UserRole("user"))
    permissions: List[str] = field(default_factory=list)
    
    # Security tracking
    failed_login_attempts: int = 0
    last_login_at: Optional[datetime] = None
    last_login_ip: Optional[str] = None
    locked_until: Optional[datetime] = None
    
    # Social authentication
    social_accounts: List[dict] = field(default_factory=list)
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Post-initialization validation and setup."""
        if not self.created_at:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Set display name if not provided
        if not self.display_name:
            if self.first_name and self.last_name:
                self.display_name = f"{self.first_name} {self.last_name}"
            elif self.username:
                self.display_name = self.username
            else:
                self.display_name = self.email.value.split('@')[0]
    
    def verify_email(self) -> None:
        """Mark user email as verified and activate account."""
        self.is_verified = True
        if self.status == UserStatus.PENDING_VERIFICATION:
            self.status = UserStatus.ACTIVE
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activate user account."""
        self.is_active = True
        self.status = UserStatus.ACTIVE
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate user account."""
        self.is_active = False
        self.status = UserStatus.INACTIVE
        self.updated_at = datetime.utcnow()
    
    def suspend(self) -> None:
        """Suspend user account."""
        self.is_active = False
        self.status = UserStatus.SUSPENDED
        self.updated_at = datetime.utcnow()
    
    def lock_account(self, duration_minutes: int = 30) -> None:
        """Lock user account for specified duration."""
        from datetime import timedelta
        self.status = UserStatus.LOCKED
        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.updated_at = datetime.utcnow()
    
    def unlock_account(self) -> None:
        """Unlock user account."""
        if self.status == UserStatus.LOCKED:
            self.status = UserStatus.ACTIVE if self.is_verified else UserStatus.PENDING_VERIFICATION
        self.locked_until = None
        self.failed_login_attempts = 0
        self.updated_at = datetime.utcnow()
    
    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.status != UserStatus.LOCKED:
            return False
        
        if self.locked_until and datetime.utcnow() >= self.locked_until:
            # Auto-unlock expired locks
            self.unlock_account()
            return False
        
        return True
    
    def record_login_attempt(self, success: bool, ip_address: Optional[str] = None) -> None:
        """Record login attempt and handle account locking."""
        if success:
            self.failed_login_attempts = 0
            self.last_login_at = datetime.utcnow()
            self.last_login_ip = ip_address
            # Auto-unlock on successful login
            if self.status == UserStatus.LOCKED:
                self.unlock_account()
        else:
            self.failed_login_attempts += 1
        
        self.updated_at = datetime.utcnow()
    
    def should_lock_account(self, max_attempts: int = 5) -> bool:
        """Check if account should be locked due to failed attempts."""
        return self.failed_login_attempts >= max_attempts and not self.is_locked()
    
    def change_password(self, new_password: Password) -> None:
        """Change user password."""
        self.password = new_password
        self.updated_at = datetime.utcnow()
    
    def update_profile(self, **kwargs) -> None:
        """Update user profile information."""
        allowed_fields = {
            'first_name', 'last_name', 'display_name', 
            'avatar_url', 'bio', 'username'
        }
        
        for field_name, value in kwargs.items():
            if field_name in allowed_fields and hasattr(self, field_name):
                setattr(self, field_name, value)
        
        self.updated_at = datetime.utcnow()
    
    def assign_role(self, role: UserRole) -> None:
        """Assign a role to the user."""
        self.role = role
        self.updated_at = datetime.utcnow()
    
    def add_permission(self, permission: str) -> None:
        """Add a permission to the user."""
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.updated_at = datetime.utcnow()
    
    def remove_permission(self, permission: str) -> None:
        """Remove a permission from the user."""
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.updated_at = datetime.utcnow()
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in self.permissions or self.role.has_permission(permission)
    
    def can_access_resource(self, required_role: str, required_permissions: List[str] = None) -> bool:
        """Check if user can access a resource based on role and permissions."""
        # Check role hierarchy
        if not self.role.can_access_role(required_role):
            return False
        
        # Check specific permissions if required
        if required_permissions:
            return all(self.has_permission(perm) for perm in required_permissions)
        
        return True
    
    def add_social_account(self, provider: str, provider_id: str, data: dict = None) -> None:
        """Add a social authentication account."""
        social_account = {
            'provider': provider,
            'provider_id': provider_id,
            'data': data or {},
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Remove existing account for same provider
        self.social_accounts = [
            acc for acc in self.social_accounts 
            if acc['provider'] != provider
        ]
        
        self.social_accounts.append(social_account)
        self.updated_at = datetime.utcnow()
    
    def get_social_account(self, provider: str) -> Optional[dict]:
        """Get social account for a specific provider."""
        for account in self.social_accounts:
            if account['provider'] == provider:
                return account
        return None
    
    def remove_social_account(self, provider: str) -> bool:
        """Remove social account for a specific provider."""
        original_count = len(self.social_accounts)
        self.social_accounts = [
            acc for acc in self.social_accounts 
            if acc['provider'] != provider
        ]
        
        if len(self.social_accounts) < original_count:
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def to_dict(self) -> dict:
        """Convert user entity to dictionary representation."""
        return {
            'id': self.id,
            'email': self.email.value,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'display_name': self.display_name,
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            'role': self.role.value,
            'permissions': self.permissions,
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'status': self.status.value,
            'failed_login_attempts': self.failed_login_attempts,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'last_login_ip': self.last_login_ip,
            'locked_until': self.locked_until.isoformat() if self.locked_until else None,
            'social_accounts': self.social_accounts,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __str__(self) -> str:
        """String representation of user."""
        return f"User(id={self.id}, email={self.email.value}, role={self.role.value})"
    
    def __repr__(self) -> str:
        """Detailed string representation of user."""
        return (
            f"User(id={self.id}, email={self.email.value}, username={self.username}, "
            f"role={self.role.value}, status={self.status.value}, "
            f"is_verified={self.is_verified}, is_active={self.is_active})"
        )

