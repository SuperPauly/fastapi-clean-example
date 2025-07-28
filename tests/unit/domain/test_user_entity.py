"""
Tests for User Entity - Domain Layer

This module contains comprehensive tests for the User entity following
hexagonal architecture testing principles.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from src.domain.entities.user import User, UserStatus
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import Password
from src.domain.value_objects.user_role import UserRole


class TestUserEntity:
    """Test cases for User entity."""
    
    def test_user_creation_with_defaults(self):
        """Test user creation with default values."""
        email = Email("test@example.com")
        user = User(email=email)
        
        assert user.email == email
        assert user.is_verified is False
        assert user.is_active is True
        assert user.status == UserStatus.PENDING_VERIFICATION
        assert user.role.value == "user"
        assert user.failed_login_attempts == 0
        assert user.permissions == []
        assert user.social_accounts == []
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_user_creation_with_all_fields(self):
        """Test user creation with all fields specified."""
        email = Email("john.doe@example.com")
        password = Mock(spec=Password)
        role = UserRole("admin")
        
        user = User(
            email=email,
            password=password,
            username="johndoe",
            first_name="John",
            last_name="Doe",
            role=role,
            is_verified=True,
            is_active=True,
            status=UserStatus.ACTIVE
        )
        
        assert user.email == email
        assert user.password == password
        assert user.username == "johndoe"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.display_name == "John Doe"
        assert user.role == role
        assert user.is_verified is True
        assert user.is_active is True
        assert user.status == UserStatus.ACTIVE
    
    def test_display_name_generation(self):
        """Test automatic display name generation."""
        email = Email("test@example.com")
        
        # Test with first and last name
        user1 = User(email=email, first_name="John", last_name="Doe")
        assert user1.display_name == "John Doe"
        
        # Test with username only
        user2 = User(email=Email("user@example.com"), username="johndoe")
        assert user2.display_name == "johndoe"
        
        # Test with email only
        user3 = User(email=Email("jane@example.com"))
        assert user3.display_name == "jane"
    
    def test_verify_email(self):
        """Test email verification."""
        email = Email("test@example.com")
        user = User(email=email, status=UserStatus.PENDING_VERIFICATION)
        
        assert not user.is_verified
        assert user.status == UserStatus.PENDING_VERIFICATION
        
        user.verify_email()
        
        assert user.is_verified
        assert user.status == UserStatus.ACTIVE
        assert user.updated_at is not None
    
    def test_activate_user(self):
        """Test user activation."""
        email = Email("test@example.com")
        user = User(email=email, is_active=False, status=UserStatus.INACTIVE)
        
        user.activate()
        
        assert user.is_active
        assert user.status == UserStatus.ACTIVE
    
    def test_deactivate_user(self):
        """Test user deactivation."""
        email = Email("test@example.com")
        user = User(email=email, is_active=True, status=UserStatus.ACTIVE)
        
        user.deactivate()
        
        assert not user.is_active
        assert user.status == UserStatus.INACTIVE
    
    def test_suspend_user(self):
        """Test user suspension."""
        email = Email("test@example.com")
        user = User(email=email, is_active=True, status=UserStatus.ACTIVE)
        
        user.suspend()
        
        assert not user.is_active
        assert user.status == UserStatus.SUSPENDED
    
    def test_lock_account(self):
        """Test account locking."""
        email = Email("test@example.com")
        user = User(email=email, status=UserStatus.ACTIVE)
        
        user.lock_account(duration_minutes=30)
        
        assert user.status == UserStatus.LOCKED
        assert user.locked_until is not None
        assert user.locked_until > datetime.utcnow()
    
    def test_unlock_account(self):
        """Test account unlocking."""
        email = Email("test@example.com")
        user = User(email=email, status=UserStatus.LOCKED, failed_login_attempts=5)
        user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        
        user.unlock_account()
        
        assert user.status == UserStatus.ACTIVE
        assert user.locked_until is None
        assert user.failed_login_attempts == 0
    
    def test_is_locked_with_active_lock(self):
        """Test is_locked with active lock."""
        email = Email("test@example.com")
        user = User(email=email, status=UserStatus.LOCKED)
        user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        
        assert user.is_locked()
    
    def test_is_locked_with_expired_lock(self):
        """Test is_locked with expired lock (should auto-unlock)."""
        email = Email("test@example.com")
        user = User(email=email, status=UserStatus.LOCKED, is_verified=True)
        user.locked_until = datetime.utcnow() - timedelta(minutes=1)
        
        assert not user.is_locked()
        assert user.status == UserStatus.ACTIVE
    
    def test_record_successful_login_attempt(self):
        """Test recording successful login attempt."""
        email = Email("test@example.com")
        user = User(email=email, failed_login_attempts=3)
        
        user.record_login_attempt(success=True, ip_address="192.168.1.1")
        
        assert user.failed_login_attempts == 0
        assert user.last_login_at is not None
        assert user.last_login_ip == "192.168.1.1"
    
    def test_record_failed_login_attempt(self):
        """Test recording failed login attempt."""
        email = Email("test@example.com")
        user = User(email=email, failed_login_attempts=2)
        
        user.record_login_attempt(success=False)
        
        assert user.failed_login_attempts == 3
        assert user.last_login_at is None
    
    def test_should_lock_account(self):
        """Test should_lock_account logic."""
        email = Email("test@example.com")
        user = User(email=email, failed_login_attempts=5)
        
        assert user.should_lock_account(max_attempts=5)
        
        user.failed_login_attempts = 3
        assert not user.should_lock_account(max_attempts=5)
    
    def test_change_password(self):
        """Test password change."""
        email = Email("test@example.com")
        user = User(email=email)
        new_password = Mock(spec=Password)
        
        user.change_password(new_password)
        
        assert user.password == new_password
        assert user.updated_at is not None
    
    def test_update_profile(self):
        """Test profile update."""
        email = Email("test@example.com")
        user = User(email=email)
        
        user.update_profile(
            first_name="John",
            last_name="Doe",
            bio="Software Developer"
        )
        
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.bio == "Software Developer"
        assert user.updated_at is not None
    
    def test_assign_role(self):
        """Test role assignment."""
        email = Email("test@example.com")
        user = User(email=email)
        admin_role = UserRole("admin")
        
        user.assign_role(admin_role)
        
        assert user.role == admin_role
        assert user.updated_at is not None
    
    def test_add_permission(self):
        """Test adding permission."""
        email = Email("test@example.com")
        user = User(email=email)
        
        user.add_permission("user:create")
        
        assert "user:create" in user.permissions
        assert user.updated_at is not None
        
        # Test adding duplicate permission
        user.add_permission("user:create")
        assert user.permissions.count("user:create") == 1
    
    def test_remove_permission(self):
        """Test removing permission."""
        email = Email("test@example.com")
        user = User(email=email, permissions=["user:create", "user:read"])
        
        user.remove_permission("user:create")
        
        assert "user:create" not in user.permissions
        assert "user:read" in user.permissions
        assert user.updated_at is not None
    
    def test_has_permission(self):
        """Test permission checking."""
        email = Email("test@example.com")
        role = Mock(spec=UserRole)
        role.has_permission.return_value = False
        user = User(email=email, role=role, permissions=["user:create"])
        
        assert user.has_permission("user:create")
        assert not user.has_permission("user:delete")
        
        # Test role-based permission
        role.has_permission.return_value = True
        assert user.has_permission("admin:access")
    
    def test_can_access_resource(self):
        """Test resource access checking."""
        email = Email("test@example.com")
        role = Mock(spec=UserRole)
        role.can_access_role.return_value = True
        user = User(email=email, role=role, permissions=["resource:read"])
        
        # Test role-based access
        assert user.can_access_resource("user")
        
        # Test permission-based access
        user.has_permission = Mock(return_value=True)
        assert user.can_access_resource("admin", ["resource:read"])
        
        # Test failed role access
        role.can_access_role.return_value = False
        assert not user.can_access_resource("superuser")
    
    def test_add_social_account(self):
        """Test adding social account."""
        email = Email("test@example.com")
        user = User(email=email)
        
        user.add_social_account("google", "123456", {"name": "John Doe"})
        
        assert len(user.social_accounts) == 1
        assert user.social_accounts[0]["provider"] == "google"
        assert user.social_accounts[0]["provider_id"] == "123456"
        assert user.social_accounts[0]["data"]["name"] == "John Doe"
        assert user.updated_at is not None
    
    def test_add_social_account_replaces_existing(self):
        """Test that adding social account replaces existing one for same provider."""
        email = Email("test@example.com")
        user = User(email=email)
        
        user.add_social_account("google", "123456", {"name": "John Doe"})
        user.add_social_account("google", "789012", {"name": "John Smith"})
        
        assert len(user.social_accounts) == 1
        assert user.social_accounts[0]["provider_id"] == "789012"
        assert user.social_accounts[0]["data"]["name"] == "John Smith"
    
    def test_get_social_account(self):
        """Test getting social account."""
        email = Email("test@example.com")
        user = User(email=email)
        user.add_social_account("google", "123456", {"name": "John Doe"})
        
        google_account = user.get_social_account("google")
        assert google_account is not None
        assert google_account["provider_id"] == "123456"
        
        github_account = user.get_social_account("github")
        assert github_account is None
    
    def test_remove_social_account(self):
        """Test removing social account."""
        email = Email("test@example.com")
        user = User(email=email)
        user.add_social_account("google", "123456", {"name": "John Doe"})
        user.add_social_account("github", "789012", {"login": "johndoe"})
        
        assert len(user.social_accounts) == 2
        
        success = user.remove_social_account("google")
        assert success
        assert len(user.social_accounts) == 1
        assert user.social_accounts[0]["provider"] == "github"
        
        # Test removing non-existent account
        success = user.remove_social_account("facebook")
        assert not success
        assert len(user.social_accounts) == 1
    
    def test_to_dict(self):
        """Test user serialization to dictionary."""
        email = Email("test@example.com")
        role = UserRole("admin")
        user = User(
            id=1,
            email=email,
            username="johndoe",
            first_name="John",
            last_name="Doe",
            role=role,
            permissions=["user:create"],
            is_verified=True,
            is_active=True,
            status=UserStatus.ACTIVE
        )
        
        user_dict = user.to_dict()
        
        assert user_dict["id"] == 1
        assert user_dict["email"] == "test@example.com"
        assert user_dict["username"] == "johndoe"
        assert user_dict["first_name"] == "John"
        assert user_dict["last_name"] == "Doe"
        assert user_dict["role"] == "admin"
        assert user_dict["permissions"] == ["user:create"]
        assert user_dict["is_verified"] is True
        assert user_dict["is_active"] is True
        assert user_dict["status"] == "active"
    
    def test_string_representations(self):
        """Test string representations of user."""
        email = Email("test@example.com")
        user = User(id=1, email=email, username="johndoe")
        
        str_repr = str(user)
        assert "User(id=1" in str_repr
        assert "test@example.com" in str_repr
        assert "role=user" in str_repr
        
        repr_str = repr(user)
        assert "User(id=1" in repr_str
        assert "test@example.com" in repr_str
        assert "username=johndoe" in repr_str
        assert "status=pending_verification" in repr_str


@pytest.fixture
def sample_user():
    """Fixture providing a sample user for testing."""
    email = Email("test@example.com")
    return User(
        id=1,
        email=email,
        username="testuser",
        first_name="Test",
        last_name="User",
        is_verified=True,
        is_active=True,
        status=UserStatus.ACTIVE
    )


class TestUserEntityIntegration:
    """Integration tests for User entity with other domain objects."""
    
    def test_user_with_real_email_value_object(self):
        """Test user with real Email value object."""
        email = Email("valid@example.com")
        user = User(email=email)
        
        assert user.email.value == "valid@example.com"
        assert user.email.get_domain() == "example.com"
    
    def test_user_with_real_role_value_object(self):
        """Test user with real UserRole value object."""
        email = Email("admin@example.com")
        admin_role = UserRole("admin")
        user = User(email=email, role=admin_role)
        
        assert user.role.value == "admin"
        assert user.role.hierarchy_level == 3
        assert user.role.has_permission("user:read_others_profile")
    
    def test_user_role_permission_integration(self):
        """Test integration between user permissions and role permissions."""
        email = Email("user@example.com")
        user_role = UserRole("user")
        user = User(email=email, role=user_role, permissions=["custom:permission"])
        
        # Test direct permission
        assert user.has_permission("custom:permission")
        
        # Test role-based permission
        assert user.has_permission("user:read_own_profile")
        
        # Test non-existent permission
        assert not user.has_permission("admin:delete_users")
    
    def test_user_lifecycle_workflow(self, sample_user):
        """Test complete user lifecycle workflow."""
        user = sample_user
        
        # Initial state
        assert user.is_active
        assert user.is_verified
        assert user.status == UserStatus.ACTIVE
        
        # Suspend user
        user.suspend()
        assert not user.is_active
        assert user.status == UserStatus.SUSPENDED
        
        # Reactivate user
        user.activate()
        assert user.is_active
        assert user.status == UserStatus.ACTIVE
        
        # Lock account due to failed attempts
        for _ in range(5):
            user.record_login_attempt(success=False)
        
        user.lock_account()
        assert user.status == UserStatus.LOCKED
        assert user.is_locked()
        
        # Unlock account
        user.unlock_account()
        assert user.status == UserStatus.ACTIVE
        assert not user.is_locked()
        assert user.failed_login_attempts == 0

