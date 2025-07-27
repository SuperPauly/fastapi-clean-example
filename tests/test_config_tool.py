"""Tests for the configuration management tool."""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# Import the configuration tool components
import sys
sys.path.append('.')
from manage_config import (
    ConfigurationSet,
    ConfigurationItem,
    ConfigurationKey,
    ConfigurationValue,
    ConfigurationFormat,
    Environment,
    CreateConfigurationCommand,
    UpdateConfigurationCommand,
    DeleteConfigurationCommand,
    CreateConfigurationUseCase,
    UpdateConfigurationUseCase,
    DeleteConfigurationUseCase,
    ConfigurationDomainService,
    ConfigurationValidator,
)


class TestDomainLayer:
    """Test the domain layer components."""
    
    def test_configuration_key_validation(self):
        """Test configuration key validation."""
        # Valid key
        key = ConfigurationKey("VALID_KEY")
        assert key.name == "VALID_KEY"
        
        # Invalid keys
        with pytest.raises(ValueError):
            ConfigurationKey("")
        
        with pytest.raises(ValueError):
            ConfigurationKey("invalid key with spaces")
    
    def test_configuration_value_creation(self):
        """Test configuration value creation and type detection."""
        # String value
        str_value = ConfigurationValue("test_string")
        assert str_value.value == "test_string"
        assert str_value.value_type == "str"
        
        # Boolean value
        bool_value = ConfigurationValue(True)
        assert bool_value.value is True
        assert bool_value.value_type == "bool"
        
        # Integer value
        int_value = ConfigurationValue(42)
        assert int_value.value == 42
        assert int_value.value_type == "int"
    
    def test_configuration_item_sensitivity_detection(self):
        """Test sensitive data detection."""
        # Sensitive key
        sensitive_item = ConfigurationItem(
            key=ConfigurationKey("SECRET_KEY"),
            value=ConfigurationValue("secret_value")
        )
        assert sensitive_item.is_sensitive() is True
        
        # Non-sensitive key
        normal_item = ConfigurationItem(
            key=ConfigurationKey("PROJECT_NAME"),
            value=ConfigurationValue("MyProject")
        )
        assert normal_item.is_sensitive() is False
    
    def test_configuration_set_operations(self):
        """Test configuration set CRUD operations."""
        config_set = ConfigurationSet("TestProject", ConfigurationFormat.TOML)
        
        # Add item
        item = ConfigurationItem(
            key=ConfigurationKey("TEST_KEY"),
            value=ConfigurationValue("test_value")
        )
        config_set.add_item(item)
        
        assert len(config_set.items) == 1
        assert config_set.get_item("TEST_KEY") is not None
        
        # Remove item
        removed = config_set.remove_item("TEST_KEY")
        assert removed is True
        assert len(config_set.items) == 0
        
        # Remove non-existent item
        removed = config_set.remove_item("NON_EXISTENT")
        assert removed is False
    
    def test_configuration_set_environment_filtering(self):
        """Test filtering items by environment."""
        config_set = ConfigurationSet("TestProject", ConfigurationFormat.TOML)
        
        # Add items for different environments
        dev_item = ConfigurationItem(
            key=ConfigurationKey("DEBUG"),
            value=ConfigurationValue(True),
            environment=Environment.DEVELOPMENT
        )
        prod_item = ConfigurationItem(
            key=ConfigurationKey("DEBUG"),
            value=ConfigurationValue(False),
            environment=Environment.PRODUCTION
        )
        
        config_set.add_item(dev_item)
        config_set.add_item(prod_item)
        
        # Filter by environment
        dev_items = config_set.get_items_by_environment(Environment.DEVELOPMENT)
        prod_items = config_set.get_items_by_environment(Environment.PRODUCTION)
        
        assert len(dev_items) == 1
        assert len(prod_items) == 1
        assert dev_items[0].value.value is True
        assert prod_items[0].value.value is False


class TestApplicationLayer:
    """Test the application layer use cases."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository."""
        mock = Mock()
        mock.save_configuration = AsyncMock(return_value=True)
        mock.load_configuration = AsyncMock(return_value=None)
        mock.backup_configuration = AsyncMock(return_value=True)
        return mock
    
    @pytest.fixture
    def mock_validator(self):
        """Create a mock validator."""
        mock = Mock()
        mock.validate_key = Mock(return_value=[])
        mock.validate_value = Mock(return_value=[])
        return mock
    
    @pytest.mark.asyncio
    async def test_create_configuration_use_case(self, mock_repository):
        """Test the create configuration use case."""
        use_case = CreateConfigurationUseCase(mock_repository)
        command = CreateConfigurationCommand("TestProject", ConfigurationFormat.TOML)
        
        result = await use_case.execute(command, Path.cwd())
        
        assert result.project_name == "TestProject"
        assert result.format == ConfigurationFormat.TOML
        assert len(result.items) > 0  # Should have default items
        mock_repository.save_configuration.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_configuration_use_case(self, mock_repository, mock_validator):
        """Test the update configuration use case."""
        use_case = UpdateConfigurationUseCase(mock_repository, mock_validator)
        config_set = ConfigurationSet("TestProject", ConfigurationFormat.TOML)
        
        command = UpdateConfigurationCommand(
            key_name="NEW_KEY",
            new_value="new_value",
            description="Test description"
        )
        
        result = await use_case.execute(command, config_set)
        
        assert result is True
        assert "NEW_KEY" in config_set.items
        assert config_set.items["NEW_KEY"].value.value == "new_value"
        assert config_set.items["NEW_KEY"].description == "Test description"
    
    @pytest.mark.asyncio
    async def test_delete_configuration_use_case(self, mock_repository):
        """Test the delete configuration use case."""
        use_case = DeleteConfigurationUseCase(mock_repository)
        config_set = ConfigurationSet("TestProject", ConfigurationFormat.TOML)
        
        # Add an item to delete
        item = ConfigurationItem(
            key=ConfigurationKey("TO_DELETE"),
            value=ConfigurationValue("value")
        )
        config_set.add_item(item)
        
        command = DeleteConfigurationCommand(key_name="TO_DELETE")
        result = await use_case.execute(command, config_set)
        
        assert result is True
        assert "TO_DELETE" not in config_set.items


class TestDomainService:
    """Test domain services."""
    
    def test_generate_default_config(self):
        """Test default configuration generation."""
        config_set = ConfigurationDomainService.generate_default_config(
            "TestProject", ConfigurationFormat.TOML
        )
        
        assert config_set.project_name == "TestProject"
        assert config_set.format == ConfigurationFormat.TOML
        assert len(config_set.items) > 0
        
        # Check for expected default items
        assert "PROJECT_NAME" in config_set.items
        assert "DEBUG" in config_set.items
        assert "DATABASE_URL" in config_set.items
        assert "SECRET_KEY" in config_set.items


class TestInfrastructureLayer:
    """Test infrastructure layer components."""
    
    def test_configuration_validator(self):
        """Test the configuration validator."""
        validator = ConfigurationValidator()
        
        # Valid key
        errors = validator.validate_key("VALID_KEY")
        assert len(errors) == 0
        
        # Invalid keys
        errors = validator.validate_key("")
        assert len(errors) > 0
        
        errors = validator.validate_key("invalid key")
        assert len(errors) > 0
        
        # Valid value
        errors = validator.validate_value("valid_value", "str")
        assert len(errors) == 0
        
        # Invalid values
        errors = validator.validate_value(None, "str")
        assert len(errors) > 0
        
        errors = validator.validate_value("", "str")
        assert len(errors) > 0


if __name__ == "__main__":
    pytest.main([__file__])
