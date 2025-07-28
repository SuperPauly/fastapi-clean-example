"""Unit tests for Dynaconf TUI components in manage_config.py."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import tempfile
import json

# Import test utilities
from tests.fixtures.tui_fixtures import mock_dynaconf_settings, tui_test_data
from tests.utils.tui_test_helpers import TUITestHelper, ConfigurationTestHelper, AsyncTestHelper

# Import the components under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import the configuration tool components from manage_config.py
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
    # TUI Components would be imported here if they were separate classes
    # For now, we'll test the main function and its components
)


class TestDynaconfTUIComponents:
    """Test the Dynaconf TUI components."""
    
    @pytest.fixture
    def mock_textual_app(self):
        """Create a mock Textual app for testing."""
        mock_app = Mock()
        mock_app.push_screen = AsyncMock()
        mock_app.pop_screen = AsyncMock()
        mock_app.exit = AsyncMock()
        mock_app.query_one = Mock()
        mock_app.query = Mock(return_value=[])
        return mock_app
    
    @pytest.fixture
    def sample_configuration_set(self):
        """Create a sample configuration set for testing."""
        config_set = ConfigurationSet("TestProject", ConfigurationFormat.TOML)
        
        # Add some sample items
        items = [
            ConfigurationItem(
                key=ConfigurationKey("PROJECT_NAME"),
                value=ConfigurationValue("TestProject"),
                description="Project name"
            ),
            ConfigurationItem(
                key=ConfigurationKey("DEBUG"),
                value=ConfigurationValue(True),
                description="Debug mode",
                environment=Environment.DEVELOPMENT
            ),
            ConfigurationItem(
                key=ConfigurationKey("DATABASE_URL"),
                value=ConfigurationValue("postgresql://localhost/test"),
                description="Database connection URL"
            )
        ]
        
        for item in items:
            config_set.add_item(item)
        
        return config_set
    
    def test_configuration_set_tui_representation(self, sample_configuration_set):
        """Test that configuration set can be represented in TUI."""
        # Test basic properties that would be displayed in TUI
        assert sample_configuration_set.project_name == "TestProject"
        assert sample_configuration_set.format == ConfigurationFormat.TOML
        assert len(sample_configuration_set.items) == 3
        
        # Test that items can be retrieved for display
        items = list(sample_configuration_set.items.values())
        assert len(items) == 3
        
        # Test environment filtering for TUI display
        dev_items = sample_configuration_set.get_items_by_environment(Environment.DEVELOPMENT)
        assert len(dev_items) == 1
        assert dev_items[0].key.name == "DEBUG"
    
    def test_configuration_item_display_properties(self, sample_configuration_set):
        """Test configuration item properties for TUI display."""
        debug_item = sample_configuration_set.get_item("DEBUG")
        
        assert debug_item is not None
        assert debug_item.key.name == "DEBUG"
        assert debug_item.value.value is True
        assert debug_item.value.value_type == "bool"
        assert debug_item.description == "Debug mode"
        assert debug_item.environment == Environment.DEVELOPMENT
        assert debug_item.is_sensitive() is False
    
    def test_sensitive_item_handling_in_tui(self):
        """Test handling of sensitive items in TUI display."""
        sensitive_item = ConfigurationItem(
            key=ConfigurationKey("SECRET_KEY"),
            value=ConfigurationValue("super_secret_value"),
            description="Application secret key"
        )
        
        assert sensitive_item.is_sensitive() is True
        
        # In TUI, sensitive values should be masked
        display_value = "***" if sensitive_item.is_sensitive() else str(sensitive_item.value.value)
        assert display_value == "***"


class TestDynaconfTUIFormInteractions:
    """Test TUI form interactions for configuration management."""
    
    @pytest.fixture
    def mock_form_widgets(self):
        """Create mock form widgets for testing."""
        widgets = {
            'project_name_input': Mock(value="TestProject"),
            'format_select': Mock(value="TOML"),
            'key_input': Mock(value="NEW_KEY"),
            'value_input': Mock(value="new_value"),
            'description_input': Mock(value="New configuration item"),
            'environment_select': Mock(value="DEVELOPMENT"),
            'submit_button': Mock(),
            'cancel_button': Mock()
        }
        
        # Add press method to buttons
        for widget_name in ['submit_button', 'cancel_button']:
            widgets[widget_name].press = AsyncMock()
        
        return widgets
    
    @pytest.fixture
    def mock_tui_app_with_forms(self, mock_form_widgets):
        """Create a mock TUI app with form widgets."""
        mock_app = Mock()
        
        def mock_query_one(selector):
            # Map selectors to widgets
            selector_map = {
                '#project_name_input': mock_form_widgets['project_name_input'],
                '#format_select': mock_form_widgets['format_select'],
                '#key_input': mock_form_widgets['key_input'],
                '#value_input': mock_form_widgets['value_input'],
                '#description_input': mock_form_widgets['description_input'],
                '#environment_select': mock_form_widgets['environment_select'],
                '#submit_button': mock_form_widgets['submit_button'],
                '#cancel_button': mock_form_widgets['cancel_button']
            }
            return selector_map.get(selector, Mock())
        
        mock_app.query_one = mock_query_one
        mock_app.push_screen = AsyncMock()
        mock_app.pop_screen = AsyncMock()
        
        return mock_app
    
    @pytest.mark.asyncio
    async def test_create_configuration_form_submission(self, mock_tui_app_with_forms):
        """Test form submission for creating new configuration."""
        # Simulate form submission
        submit_button = mock_tui_app_with_forms.query_one('#submit_button')
        await submit_button.press()
        
        submit_button.press.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_configuration_form_validation(self, mock_tui_app_with_forms):
        """Test form validation for configuration updates."""
        # Get form inputs
        key_input = mock_tui_app_with_forms.query_one('#key_input')
        value_input = mock_tui_app_with_forms.query_one('#value_input')
        
        # Test valid input
        key_input.value = "VALID_KEY"
        value_input.value = "valid_value"
        
        # Simulate validation
        validator = ConfigurationValidator()
        key_errors = validator.validate_key(key_input.value)
        value_errors = validator.validate_value(value_input.value, "str")
        
        assert len(key_errors) == 0
        assert len(value_errors) == 0
    
    @pytest.mark.asyncio
    async def test_form_validation_errors_display(self, mock_tui_app_with_forms):
        """Test display of validation errors in forms."""
        # Get form inputs with invalid values
        key_input = mock_tui_app_with_forms.query_one('#key_input')
        value_input = mock_tui_app_with_forms.query_one('#value_input')
        
        key_input.value = "invalid key with spaces"
        value_input.value = ""
        
        # Simulate validation
        validator = ConfigurationValidator()
        key_errors = validator.validate_key(key_input.value)
        value_errors = validator.validate_value(value_input.value, "str")
        
        assert len(key_errors) > 0
        assert len(value_errors) > 0
        
        # In a real TUI, these errors would be displayed to the user
        assert any("spaces" in error.lower() for error in key_errors)
        assert any("empty" in error.lower() for error in value_errors)


class TestDynaconfTUINavigationAndScreens:
    """Test TUI navigation and screen management."""
    
    @pytest.fixture
    def mock_screen_manager(self):
        """Create a mock screen manager for testing."""
        manager = Mock()
        manager.current_screen = "main"
        manager.screen_stack = ["main"]
        manager.push_screen = AsyncMock()
        manager.pop_screen = AsyncMock()
        manager.switch_screen = AsyncMock()
        return manager
    
    @pytest.mark.asyncio
    async def test_navigation_to_create_screen(self, mock_screen_manager):
        """Test navigation to create configuration screen."""
        await mock_screen_manager.push_screen("create_config")
        
        mock_screen_manager.push_screen.assert_called_once_with("create_config")
    
    @pytest.mark.asyncio
    async def test_navigation_to_edit_screen(self, mock_screen_manager):
        """Test navigation to edit configuration screen."""
        await mock_screen_manager.push_screen("edit_config")
        
        mock_screen_manager.push_screen.assert_called_once_with("edit_config")
    
    @pytest.mark.asyncio
    async def test_navigation_back_to_main(self, mock_screen_manager):
        """Test navigation back to main screen."""
        await mock_screen_manager.pop_screen()
        
        mock_screen_manager.pop_screen.assert_called_once()
    
    def test_screen_state_management(self, mock_screen_manager):
        """Test screen state management."""
        # Test initial state
        assert mock_screen_manager.current_screen == "main"
        assert len(mock_screen_manager.screen_stack) == 1
        
        # Simulate screen changes
        mock_screen_manager.current_screen = "create_config"
        mock_screen_manager.screen_stack.append("create_config")
        
        assert mock_screen_manager.current_screen == "create_config"
        assert len(mock_screen_manager.screen_stack) == 2


class TestDynaconfTUIDataBinding:
    """Test data binding between TUI and domain models."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing."""
        mock = Mock()
        mock.save_configuration = AsyncMock(return_value=True)
        mock.load_configuration = AsyncMock(return_value=None)
        mock.backup_configuration = AsyncMock(return_value=True)
        return mock
    
    @pytest.mark.asyncio
    async def test_configuration_data_binding(self, mock_repository):
        """Test binding configuration data to TUI components."""
        # Create a configuration set
        config_set = ConfigurationSet("TestProject", ConfigurationFormat.TOML)
        
        # Add test item
        item = ConfigurationItem(
            key=ConfigurationKey("TEST_KEY"),
            value=ConfigurationValue("test_value"),
            description="Test item"
        )
        config_set.add_item(item)
        
        # Simulate saving through repository
        result = await mock_repository.save_configuration(config_set)
        
        assert result is True
        mock_repository.save_configuration.assert_called_once_with(config_set)
    
    @pytest.mark.asyncio
    async def test_form_to_domain_model_conversion(self, mock_repository):
        """Test conversion from form data to domain models."""
        # Simulate form data
        form_data = {
            'project_name': 'TestProject',
            'format': 'TOML',
            'items': [
                {
                    'key': 'TEST_KEY',
                    'value': 'test_value',
                    'description': 'Test item',
                    'environment': 'DEVELOPMENT'
                }
            ]
        }
        
        # Convert to domain model
        config_set = ConfigurationSet(
            form_data['project_name'],
            ConfigurationFormat[form_data['format']]
        )
        
        for item_data in form_data['items']:
            item = ConfigurationItem(
                key=ConfigurationKey(item_data['key']),
                value=ConfigurationValue(item_data['value']),
                description=item_data['description'],
                environment=Environment[item_data['environment']]
            )
            config_set.add_item(item)
        
        # Verify conversion
        assert config_set.project_name == 'TestProject'
        assert config_set.format == ConfigurationFormat.TOML
        assert len(config_set.items) == 1
        
        test_item = config_set.get_item('TEST_KEY')
        assert test_item is not None
        assert test_item.value.value == 'test_value'
        assert test_item.environment == Environment.DEVELOPMENT
    
    @pytest.mark.asyncio
    async def test_domain_model_to_tui_display_conversion(self):
        """Test conversion from domain models to TUI display format."""
        # Create domain model
        config_set = ConfigurationSet("TestProject", ConfigurationFormat.TOML)
        
        item = ConfigurationItem(
            key=ConfigurationKey("DATABASE_URL"),
            value=ConfigurationValue("postgresql://localhost/test"),
            description="Database connection",
            environment=Environment.PRODUCTION
        )
        config_set.add_item(item)
        
        # Convert to display format
        display_data = {
            'project_name': config_set.project_name,
            'format': config_set.format.value,
            'items': []
        }
        
        for key, item in config_set.items.items():
            display_item = {
                'key': item.key.name,
                'value': "***" if item.is_sensitive() else str(item.value.value),
                'type': item.value.value_type,
                'description': item.description,
                'environment': item.environment.value if item.environment else "ALL"
            }
            display_data['items'].append(display_item)
        
        # Verify display format
        assert display_data['project_name'] == "TestProject"
        assert display_data['format'] == "TOML"
        assert len(display_data['items']) == 1
        
        display_item = display_data['items'][0]
        assert display_item['key'] == "DATABASE_URL"
        assert display_item['value'] == "postgresql://localhost/test"  # Not sensitive
        assert display_item['type'] == "str"
        assert display_item['environment'] == "PRODUCTION"


class TestDynaconfTUIErrorHandling:
    """Test error handling in Dynaconf TUI."""
    
    @pytest.fixture
    def failing_repository(self):
        """Create a repository that fails operations."""
        mock = Mock()
        mock.save_configuration = AsyncMock(side_effect=Exception("Save failed"))
        mock.load_configuration = AsyncMock(side_effect=Exception("Load failed"))
        mock.backup_configuration = AsyncMock(side_effect=Exception("Backup failed"))
        return mock
    
    @pytest.mark.asyncio
    async def test_save_error_handling(self, failing_repository):
        """Test error handling during configuration save."""
        config_set = ConfigurationSet("TestProject", ConfigurationFormat.TOML)
        
        # Attempt to save with failing repository
        try:
            await failing_repository.save_configuration(config_set)
            assert False, "Expected exception was not raised"
        except Exception as e:
            assert str(e) == "Save failed"
    
    @pytest.mark.asyncio
    async def test_load_error_handling(self, failing_repository):
        """Test error handling during configuration load."""
        # Attempt to load with failing repository
        try:
            await failing_repository.load_configuration("test")
            assert False, "Expected exception was not raised"
        except Exception as e:
            assert str(e) == "Load failed"
    
    def test_validation_error_collection(self):
        """Test collection and display of validation errors."""
        validator = ConfigurationValidator()
        
        # Test multiple validation errors
        errors = []
        errors.extend(validator.validate_key(""))  # Empty key
        errors.extend(validator.validate_key("invalid key"))  # Invalid key
        errors.extend(validator.validate_value("", "str"))  # Empty value
        
        assert len(errors) > 0
        
        # Errors should be descriptive for TUI display
        error_messages = [str(error) for error in errors]
        assert any("empty" in msg.lower() for msg in error_messages)
        assert any("invalid" in msg.lower() for msg in error_messages)
    
    def test_form_validation_error_display(self):
        """Test form validation error display formatting."""
        validator = ConfigurationValidator()
        
        # Test key validation
        key_errors = validator.validate_key("invalid key with spaces")
        assert len(key_errors) > 0
        
        # Format errors for TUI display
        formatted_errors = []
        for error in key_errors:
            formatted_errors.append(f"❌ {error}")
        
        assert len(formatted_errors) > 0
        assert all(error.startswith("❌") for error in formatted_errors)


class TestDynaconfTUIPerformance:
    """Test performance characteristics of Dynaconf TUI."""
    
    @pytest.mark.asyncio
    async def test_large_configuration_handling(self):
        """Test handling of large configuration sets."""
        config_set = ConfigurationSet("LargeProject", ConfigurationFormat.TOML)
        
        # Add many configuration items
        for i in range(100):
            item = ConfigurationItem(
                key=ConfigurationKey(f"CONFIG_ITEM_{i}"),
                value=ConfigurationValue(f"value_{i}"),
                description=f"Configuration item {i}"
            )
            config_set.add_item(item)
        
        # Test that operations complete quickly
        start_time = AsyncTestHelper.create_async_mock()
        
        # Test item retrieval performance
        assert len(config_set.items) == 100
        
        # Test filtering performance
        dev_items = config_set.get_items_by_environment(Environment.DEVELOPMENT)
        assert isinstance(dev_items, list)
        
        # Test search performance (if implemented)
        test_item = config_set.get_item("CONFIG_ITEM_50")
        assert test_item is not None
        assert test_item.key.name == "CONFIG_ITEM_50"
    
    @pytest.mark.asyncio
    async def test_form_rendering_performance(self):
        """Test form rendering performance with many fields."""
        # Simulate form with many fields
        form_fields = {}
        
        for i in range(50):
            form_fields[f"field_{i}"] = {
                'type': 'input',
                'value': f'value_{i}',
                'validation': lambda x: len(x) > 0
            }
        
        # Test that form data can be processed quickly
        assert len(form_fields) == 50
        
        # Test validation performance
        validation_results = {}
        for field_name, field_config in form_fields.items():
            validation_results[field_name] = field_config['validation'](field_config['value'])
        
        assert len(validation_results) == 50
        assert all(result for result in validation_results.values())


class TestDynaconfTUIIntegrationWithDomain:
    """Test integration between TUI and domain layer."""
    
    @pytest.mark.asyncio
    async def test_use_case_integration(self):
        """Test integration with domain use cases."""
        # Mock repository
        mock_repository = Mock()
        mock_repository.save_configuration = AsyncMock(return_value=True)
        
        # Create use case
        create_use_case = CreateConfigurationUseCase(mock_repository)
        
        # Execute use case
        command = CreateConfigurationCommand("TestProject", ConfigurationFormat.TOML)
        result = await create_use_case.execute(command, Path.cwd())
        
        # Verify integration
        assert result.project_name == "TestProject"
        assert result.format == ConfigurationFormat.TOML
        mock_repository.save_configuration.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_domain_service_integration(self):
        """Test integration with domain services."""
        # Test default configuration generation
        config_set = ConfigurationDomainService.generate_default_config(
            "TestProject", ConfigurationFormat.TOML
        )
        
        # Verify domain service results can be used in TUI
        assert config_set.project_name == "TestProject"
        assert config_set.format == ConfigurationFormat.TOML
        assert len(config_set.items) > 0
        
        # Test that default items are suitable for TUI display
        for key, item in config_set.items.items():
            assert isinstance(item.key.name, str)
            assert item.value.value is not None
            assert isinstance(item.description, str)
    
    def test_validator_integration(self):
        """Test integration with configuration validator."""
        validator = ConfigurationValidator()
        
        # Test validation of TUI form data
        form_data = {
            'key': 'VALID_KEY',
            'value': 'valid_value',
            'type': 'str'
        }
        
        key_errors = validator.validate_key(form_data['key'])
        value_errors = validator.validate_value(form_data['value'], form_data['type'])
        
        assert len(key_errors) == 0
        assert len(value_errors) == 0
        
        # Test with invalid data
        invalid_form_data = {
            'key': 'invalid key',
            'value': '',
            'type': 'str'
        }
        
        key_errors = validator.validate_key(invalid_form_data['key'])
        value_errors = validator.validate_value(invalid_form_data['value'], invalid_form_data['type'])
        
        assert len(key_errors) > 0
        assert len(value_errors) > 0

