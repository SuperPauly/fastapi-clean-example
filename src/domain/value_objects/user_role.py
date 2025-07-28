"""
UserRole Value Object - Domain Layer

This module contains the UserRole value object that encapsulates role-based
access control (RBAC) logic following Domain-Driven Design principles.
"""

from dataclasses import dataclass
from typing import List, Dict, Set, Optional
from enum import Enum


class DefaultRole(Enum):
    """Default system roles with hierarchy."""
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPERUSER = "superuser"


@dataclass(frozen=True)
class Permission:
    """Permission value object."""
    name: str
    description: str = ""
    resource: str = ""
    action: str = ""
    
    def __post_init__(self):
        """Validate permission on creation."""
        if not self.name:
            raise ValueError("Permission name cannot be empty")
        
        if not self.name.replace('_', '').replace(':', '').replace('.', '').isalnum():
            raise ValueError("Permission name can only contain alphanumeric characters, underscores, colons, and dots")


@dataclass(frozen=True)
class UserRole:
    """
    UserRole value object that encapsulates role-based access control.
    
    This value object follows hexagonal architecture principles by:
    - Being immutable (frozen dataclass)
    - Containing RBAC business logic
    - Being framework-agnostic
    - Encapsulating role-related business rules
    """
    
    value: str
    permissions: Set[str] = None
    hierarchy_level: int = 1
    description: str = ""
    
    def __post_init__(self):
        """Initialize role with default permissions and validation."""
        if not self.value:
            raise ValueError("Role value cannot be empty")
        
        # Normalize role value
        normalized_value = self.value.lower().strip()
        object.__setattr__(self, 'value', normalized_value)
        
        # Initialize permissions if not provided
        if self.permissions is None:
            object.__setattr__(self, 'permissions', self._get_default_permissions())
        
        # Set hierarchy level if not provided
        if self.hierarchy_level == 1:  # Default value
            object.__setattr__(self, 'hierarchy_level', self._get_default_hierarchy_level())
        
        # Set description if not provided
        if not self.description:
            object.__setattr__(self, 'description', self._get_default_description())
    
    def _get_default_permissions(self) -> Set[str]:
        """Get default permissions for the role."""
        role_permissions = {
            DefaultRole.USER.value: {
                'user:read_own_profile',
                'user:update_own_profile',
                'user:delete_own_account',
                'content:read',
                'content:create_own',
                'content:update_own',
                'content:delete_own',
            },
            DefaultRole.MODERATOR.value: {
                'user:read_own_profile',
                'user:update_own_profile',
                'user:delete_own_account',
                'user:read_others_profile',
                'content:read',
                'content:create_own',
                'content:update_own',
                'content:delete_own',
                'content:moderate',
                'content:update_others',
                'content:delete_others',
                'reports:read',
                'reports:resolve',
            },
            DefaultRole.ADMIN.value: {
                'user:read_own_profile',
                'user:update_own_profile',
                'user:delete_own_account',
                'user:read_others_profile',
                'user:update_others_profile',
                'user:suspend_users',
                'user:activate_users',
                'content:read',
                'content:create_own',
                'content:update_own',
                'content:delete_own',
                'content:moderate',
                'content:update_others',
                'content:delete_others',
                'content:manage_all',
                'reports:read',
                'reports:resolve',
                'reports:manage',
                'system:read_logs',
                'system:manage_settings',
                'roles:assign_user',
                'roles:assign_moderator',
            },
            DefaultRole.SUPERUSER.value: {
                'user:*',
                'content:*',
                'reports:*',
                'system:*',
                'roles:*',
                'admin:*',
            }
        }
        
        return role_permissions.get(self.value, set())
    
    def _get_default_hierarchy_level(self) -> int:
        """Get default hierarchy level for the role."""
        hierarchy_levels = {
            DefaultRole.USER.value: 1,
            DefaultRole.MODERATOR.value: 2,
            DefaultRole.ADMIN.value: 3,
            DefaultRole.SUPERUSER.value: 4,
        }
        
        return hierarchy_levels.get(self.value, 1)
    
    def _get_default_description(self) -> str:
        """Get default description for the role."""
        descriptions = {
            DefaultRole.USER.value: "Standard user with basic permissions",
            DefaultRole.MODERATOR.value: "Moderator with content management permissions",
            DefaultRole.ADMIN.value: "Administrator with user and system management permissions",
            DefaultRole.SUPERUSER.value: "Super user with full system access",
        }
        
        return descriptions.get(self.value, f"Custom role: {self.value}")
    
    def has_permission(self, permission: str) -> bool:
        """
        Check if role has a specific permission.
        
        Args:
            permission: Permission to check
            
        Returns:
            bool: True if role has permission
        """
        if not permission:
            return False
        
        # Check for wildcard permissions
        for role_permission in self.permissions:
            if role_permission.endswith('*'):
                prefix = role_permission[:-1]
                if permission.startswith(prefix):
                    return True
            elif role_permission == permission:
                return True
        
        return False
    
    def has_any_permission(self, permissions: List[str]) -> bool:
        """
        Check if role has any of the specified permissions.
        
        Args:
            permissions: List of permissions to check
            
        Returns:
            bool: True if role has at least one permission
        """
        return any(self.has_permission(perm) for perm in permissions)
    
    def has_all_permissions(self, permissions: List[str]) -> bool:
        """
        Check if role has all of the specified permissions.
        
        Args:
            permissions: List of permissions to check
            
        Returns:
            bool: True if role has all permissions
        """
        return all(self.has_permission(perm) for perm in permissions)
    
    def can_access_role(self, required_role: str) -> bool:
        """
        Check if this role can access resources requiring another role.
        
        Args:
            required_role: Role required for access
            
        Returns:
            bool: True if this role can access the required role's resources
        """
        required_role_obj = UserRole(required_role)
        return self.hierarchy_level >= required_role_obj.hierarchy_level
    
    def can_manage_role(self, target_role: str) -> bool:
        """
        Check if this role can manage (assign/revoke) another role.
        
        Args:
            target_role: Role to manage
            
        Returns:
            bool: True if this role can manage the target role
        """
        target_role_obj = UserRole(target_role)
        
        # Can only manage roles with lower hierarchy level
        if self.hierarchy_level <= target_role_obj.hierarchy_level:
            return False
        
        # Check specific role management permissions
        manage_permission = f"roles:assign_{target_role}"
        if self.has_permission(manage_permission):
            return True
        
        # Check wildcard permissions
        if self.has_permission("roles:*"):
            return True
        
        return False
    
    def get_manageable_roles(self, available_roles: List[str]) -> List[str]:
        """
        Get list of roles that this role can manage.
        
        Args:
            available_roles: List of all available roles
            
        Returns:
            List of manageable role names
        """
        manageable = []
        
        for role_name in available_roles:
            if self.can_manage_role(role_name):
                manageable.append(role_name)
        
        return manageable
    
    def get_accessible_resources(self) -> Dict[str, List[str]]:
        """
        Get resources and actions accessible to this role.
        
        Returns:
            Dict mapping resource names to list of allowed actions
        """
        resources = {}
        
        for permission in self.permissions:
            if ':' in permission:
                resource, action = permission.split(':', 1)
                if resource not in resources:
                    resources[resource] = []
                resources[resource].append(action)
        
        return resources
    
    def is_system_role(self) -> bool:
        """
        Check if this is a system-defined role.
        
        Returns:
            bool: True if system role
        """
        system_roles = {role.value for role in DefaultRole}
        return self.value in system_roles
    
    def is_custom_role(self) -> bool:
        """
        Check if this is a custom-defined role.
        
        Returns:
            bool: True if custom role
        """
        return not self.is_system_role()
    
    def get_role_level_name(self) -> str:
        """
        Get human-readable role level name.
        
        Returns:
            str: Role level name
        """
        level_names = {
            1: "Basic",
            2: "Intermediate", 
            3: "Advanced",
            4: "Expert",
        }
        
        return level_names.get(self.hierarchy_level, f"Level {self.hierarchy_level}")
    
    def add_permission(self, permission: str) -> 'UserRole':
        """
        Create new role with additional permission.
        
        Args:
            permission: Permission to add
            
        Returns:
            New UserRole instance with added permission
        """
        new_permissions = self.permissions.copy()
        new_permissions.add(permission)
        
        return UserRole(
            value=self.value,
            permissions=new_permissions,
            hierarchy_level=self.hierarchy_level,
            description=self.description
        )
    
    def remove_permission(self, permission: str) -> 'UserRole':
        """
        Create new role with permission removed.
        
        Args:
            permission: Permission to remove
            
        Returns:
            New UserRole instance with permission removed
        """
        new_permissions = self.permissions.copy()
        new_permissions.discard(permission)
        
        return UserRole(
            value=self.value,
            permissions=new_permissions,
            hierarchy_level=self.hierarchy_level,
            description=self.description
        )
    
    def merge_permissions(self, other_role: 'UserRole') -> 'UserRole':
        """
        Create new role with permissions merged from another role.
        
        Args:
            other_role: Role to merge permissions from
            
        Returns:
            New UserRole instance with merged permissions
        """
        merged_permissions = self.permissions.union(other_role.permissions)
        
        return UserRole(
            value=self.value,
            permissions=merged_permissions,
            hierarchy_level=max(self.hierarchy_level, other_role.hierarchy_level),
            description=self.description
        )
    
    def to_dict(self) -> Dict:
        """
        Convert role to dictionary representation.
        
        Returns:
            Dict representation of role
        """
        return {
            'value': self.value,
            'permissions': list(self.permissions),
            'hierarchy_level': self.hierarchy_level,
            'description': self.description,
            'is_system_role': self.is_system_role(),
            'level_name': self.get_role_level_name(),
            'accessible_resources': self.get_accessible_resources()
        }
    
    @classmethod
    def create_custom_role(
        cls,
        name: str,
        permissions: Set[str],
        hierarchy_level: int = 1,
        description: str = ""
    ) -> 'UserRole':
        """
        Create a custom role with specified permissions.
        
        Args:
            name: Role name
            permissions: Set of permissions
            hierarchy_level: Role hierarchy level
            description: Role description
            
        Returns:
            UserRole instance
        """
        return cls(
            value=name,
            permissions=permissions,
            hierarchy_level=hierarchy_level,
            description=description or f"Custom role: {name}"
        )
    
    @classmethod
    def get_available_system_roles(cls) -> List['UserRole']:
        """
        Get all available system roles.
        
        Returns:
            List of system UserRole instances
        """
        return [cls(role.value) for role in DefaultRole]
    
    def __str__(self) -> str:
        """String representation of role."""
        return self.value
    
    def __repr__(self) -> str:
        """Detailed string representation of role."""
        return (
            f"UserRole(value='{self.value}', hierarchy_level={self.hierarchy_level}, "
            f"permissions_count={len(self.permissions)})"
        )
    
    def __eq__(self, other) -> bool:
        """Compare roles for equality."""
        if isinstance(other, UserRole):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other.lower().strip()
        return False
    
    def __hash__(self) -> int:
        """Hash function for role."""
        return hash(self.value)
    
    def __lt__(self, other) -> bool:
        """Compare roles by hierarchy level."""
        if isinstance(other, UserRole):
            return self.hierarchy_level < other.hierarchy_level
        return NotImplemented
    
    def __le__(self, other) -> bool:
        """Compare roles by hierarchy level."""
        if isinstance(other, UserRole):
            return self.hierarchy_level <= other.hierarchy_level
        return NotImplemented
    
    def __gt__(self, other) -> bool:
        """Compare roles by hierarchy level."""
        if isinstance(other, UserRole):
            return self.hierarchy_level > other.hierarchy_level
        return NotImplemented
    
    def __ge__(self, other) -> bool:
        """Compare roles by hierarchy level."""
        if isinstance(other, UserRole):
            return self.hierarchy_level >= other.hierarchy_level
        return NotImplemented

