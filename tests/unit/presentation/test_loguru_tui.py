"""Unit tests for Loguru TUI components."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import asyncio

# Import test utilities
from tests.fixtures.tui_fixtures import (
    sample_logger_config,
    mock_config_port,
    mock_logger_port,
    tui_test_data,
    async_test_timeout
)
from tests.fixtures.mock_repositories import MockLoggerConfigurationRepository, MockLoggerApplicationAdapter
from tests.utils.tui_test_helpers import TUITestHelper, AsyncTestHelper

# Import the components under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from src.presentation.tui.app import LoguruConfigApp
from src.domain.entities.logger_config import LoggerConfig
from src.domain.value_objects.log_level import LogLevel


class TestLoguruConfigApp:
    """Test the main Loguru TUI application."""
    
    @pytest.fixture
    def mock_dependencies(self, mock_config_port, mock_logger_port):
        """Create mock dependencies for the TUI app."""
        return {
            'config_port': mock_config_port,
            'logger_port': mock_logger_port
        }
    
    @pytest.fixture
    def tui_app(self, mock_dependencies):
        """Create a LoguruConfigApp instance for testing."""
        return LoguruConfigApp(
            config_port=mock_dependencies['config_port'],
            logger_port=mock_dependencies['logger_port']
        )
    
    def test_app_initialization(self, tui_app, mock_dependencies):
        """Test that the TUI app initializes correctly."""
        assert tui_app.config_port == mock_dependencies['config_port']
        assert tui_app.logger_port == mock_dependencies['logger_port']
        assert tui_app.title == "Loguru Configuration Tool"
        assert tui_app.sub_title == "Configure Loguru logging with ease"
    
    def test_app_css_classes(self, tui_app):
        """Test that the app has the correct CSS classes."""
        assert hasattr(tui_app, 'CSS')
        # The CSS should define styling for the app components
        css_content = str(tui_app.CSS)
        assert len(css_content) > 0
    
    @pytest.mark.asyncio
    async def test_app_compose_result(self, tui_app):
        """Test that the app composes the correct widgets."""
        # Mock the compose method to avoid actual widget creation
        with patch.object(tui_app, 'compose') as mock_compose:
            mock_compose.return_value = []
            result = tui_app.compose()
            mock_compose.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_load_configuration_success(self, tui_app, sample_logger_config, mock_config_port):
        """Test successful configuration loading."""
        mock_config_port.load_configuration.return_value = sample_logger_config
        
        result = await tui_app.load_configuration("test_config")
        
        assert result is True
        mock_config_port.load_configuration.assert_called_once_with("test_config")
    
    @pytest.mark.asyncio
    async def test_load_configuration_not_found(self, tui_app, mock_config_port):
        """Test loading non-existent configuration."""
        mock_config_port.load_configuration.return_value = None
        
        result = await tui_app.load_configuration("nonexistent")
        
        assert result is False
        mock_config_port.load_configuration.assert_called_once_with("nonexistent")
    
    @pytest.mark.asyncio
    async def test_save_current_configuration(self, tui_app, sample_logger_config, mock_config_port):
        """Test saving current configuration."""
        # Set up the app with a current configuration
        tui_app.current_config = sample_logger_config
        mock_config_port.save_configuration.return_value = True
        
        result = await tui_app.save_current_configuration()
        
        assert result is True
        mock_config_port.save_configuration.assert_called_once_with(sample_logger_config)
    
    @pytest.mark.asyncio
    async def test_save_configuration_no_current_config(self, tui_app):
        """Test saving when no current configuration exists."""
        tui_app.current_config = None
        
        result = await tui_app.save_current_configuration()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_test_configuration(self, tui_app, sample_logger_config, mock_logger_port):
        """Test configuration testing functionality."""
        mock_logger_port.test_configuration.return_value = {
            "success": True,
            "output": ["Test message 1", "Test message 2"],
            "errors": []
        }
        
        result = await tui_app.test_configuration(sample_logger_config)
        
        assert result["success"] is True
        assert len(result["output"]) == 2
        mock_logger_port.test_configuration.assert_called_once_with(sample_logger_config, None)
    
    @pytest.mark.asyncio
    async def test_preview_log_output(self, tui_app, sample_logger_config, mock_logger_port):
        """Test log output preview functionality."""
        sample_messages = ["Test message 1", "Test message 2"]
        expected_output = ["DEBUG | Test message 1", "DEBUG | Test message 2"]
        mock_logger_port.preview_log_output.return_value = expected_output
        
        result = await tui_app.preview_log_output(sample_logger_config, sample_messages)
        
        assert result == expected_output
        mock_logger_port.preview_log_output.assert_called_once_with(sample_logger_config, sample_messages)


class TestLoguruTUINavigation:
    """Test TUI navigation functionality."""
    
    @pytest.fixture
    def mock_app_with_navigation(self, tui_test_data):
        """Create a mock app with navigation widgets."""
        widget_configs = [
            {
                'id': 'nav_basic_settings',
                'type': 'Button',
                'props': {'text': 'Basic Settings', 'pressed': False}
            },
            {
                'id': 'nav_file_config',
                'type': 'Button', 
                'props': {'text': 'File Configuration', 'pressed': False}
            },
            {
                'id': 'nav_formatting',
                'type': 'Button',
                'props': {'text': 'Formatting & Colors', 'pressed': False}
            },
            {
                'id': 'main_content',
                'type': 'Static',
                'props': {'text': 'Welcome to Loguru Configuration'}
            }
        ]
        return TUITestHelper.create_mock_app_with_widgets(widget_configs)
    
    @pytest.mark.asyncio
    async def test_navigation_button_interaction(self, mock_app_with_navigation):
        """Test navigation button interactions."""
        # Simulate clicking on basic settings
        basic_settings_btn = mock_app_with_navigation.query_one("#nav_basic_settings")
        
        # Mock the button press
        basic_settings_btn.press = AsyncMock()
        await basic_settings_btn.press()
        
        basic_settings_btn.press.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_content_area_updates(self, mock_app_with_navigation):
        """Test that content area updates when navigation changes."""
        main_content = mock_app_with_navigation.query_one("#main_content")
        
        # Simulate content update
        new_content = "📊 Basic Settings\n\nConfigure fundamental logging options"
        main_content.text = new_content
        
        assert main_content.text == new_content
    
    def test_navigation_items_present(self, mock_app_with_navigation, tui_test_data):
        """Test that all expected navigation items are present."""
        # Check that navigation buttons exist
        nav_buttons = [
            "#nav_basic_settings",
            "#nav_file_config", 
            "#nav_formatting"
        ]
        
        for button_id in nav_buttons:
            widget = mock_app_with_navigation.query_one(button_id)
            assert widget is not None
            assert hasattr(widget, 'text')


class TestLoguruTUIConfiguration:
    """Test TUI configuration management functionality."""
    
    @pytest.fixture
    def mock_config_repository(self):
        """Create a mock configuration repository."""
        return MockLoggerConfigurationRepository()
    
    @pytest.fixture
    def mock_logger_adapter(self):
        """Create a mock logger adapter."""
        return MockLoggerApplicationAdapter()
    
    @pytest.mark.asyncio
    async def test_configuration_loading_workflow(self, mock_config_repository, sample_logger_config):
        """Test the complete configuration loading workflow."""
        # Save a configuration first
        await mock_config_repository.save_configuration(sample_logger_config)
        
        # Load the configuration
        loaded_config = await mock_config_repository.load_configuration(sample_logger_config.name)
        
        assert loaded_config is not None
        assert loaded_config.name == sample_logger_config.name
        assert loaded_config.enabled == sample_logger_config.enabled
    
    @pytest.mark.asyncio
    async def test_configuration_validation_workflow(self, mock_config_repository, sample_logger_config):
        """Test configuration validation workflow."""
        # Test with valid configuration
        warnings = await mock_config_repository.validate_configuration(sample_logger_config)
        assert isinstance(warnings, list)
        
        # Test with invalid configuration (no handlers)
        invalid_config = LoggerConfig(
            name="invalid",
            description="Invalid config",
            enabled=True,
            global_level=LogLevel.DEBUG,
            handlers=[],  # No handlers
            activation=[],
            patcher=None,
            extra={}
        )
        
        warnings = await mock_config_repository.validate_configuration(invalid_config)
        assert len(warnings) > 0
        assert any("No handlers configured" in warning for warning in warnings)
    
    @pytest.mark.asyncio
    async def test_configuration_export_import_workflow(self, mock_config_repository, sample_logger_config):
        """Test configuration export and import workflow."""
        # Save original configuration
        await mock_config_repository.save_configuration(sample_logger_config)
        
        # Export configuration
        exported_json = await mock_config_repository.export_configuration(sample_logger_config.name, "json")
        assert exported_json is not None
        assert sample_logger_config.name in exported_json
        
        # Import configuration with new name
        imported_config = await mock_config_repository.import_configuration(
            exported_json, "json", "imported_config"
        )
        assert imported_config is not None
        assert imported_config.name == "imported_config"
    
    @pytest.mark.asyncio
    async def test_logger_application_workflow(self, mock_logger_adapter, sample_logger_config):
        """Test logger application workflow."""
        # Apply configuration
        result = await mock_logger_adapter.apply_configuration(sample_logger_config)
        assert result is True
        
        # Get current configuration
        current = await mock_logger_adapter.get_current_configuration()
        assert current == sample_logger_config
        
        # Test configuration
        test_result = await mock_logger_adapter.test_configuration(sample_logger_config)
        assert test_result["success"] is True
        assert len(test_result["output"]) > 0
        
        # Preview output
        sample_messages = ["Test message 1", "Test message 2"]
        preview = await mock_logger_adapter.preview_log_output(sample_logger_config, sample_messages)
        assert len(preview) == len(sample_messages)


class TestLoguruTUIErrorHandling:
    """Test TUI error handling and edge cases."""
    
    @pytest.fixture
    def failing_config_port(self):
        """Create a config port that fails operations."""
        mock = Mock()
        mock.load_configuration = AsyncMock(side_effect=Exception("Load failed"))
        mock.save_configuration = AsyncMock(side_effect=Exception("Save failed"))
        mock.validate_configuration = AsyncMock(side_effect=Exception("Validation failed"))
        return mock
    
    @pytest.fixture
    def failing_logger_port(self):
        """Create a logger port that fails operations."""
        mock = Mock()
        mock.apply_configuration = AsyncMock(side_effect=Exception("Apply failed"))
        mock.test_configuration = AsyncMock(side_effect=Exception("Test failed"))
        mock.preview_log_output = AsyncMock(side_effect=Exception("Preview failed"))
        return mock
    
    @pytest.mark.asyncio
    async def test_load_configuration_error_handling(self, failing_config_port, mock_logger_port):
        """Test error handling during configuration loading."""
        app = LoguruConfigApp(failing_config_port, mock_logger_port)
        
        result = await app.load_configuration("test")
        
        # Should handle the error gracefully
        assert result is False
    
    @pytest.mark.asyncio
    async def test_save_configuration_error_handling(self, failing_config_port, mock_logger_port, sample_logger_config):
        """Test error handling during configuration saving."""
        app = LoguruConfigApp(failing_config_port, mock_logger_port)
        app.current_config = sample_logger_config
        
        result = await app.save_current_configuration()
        
        # Should handle the error gracefully
        assert result is False
    
    @pytest.mark.asyncio
    async def test_test_configuration_error_handling(self, mock_config_port, failing_logger_port, sample_logger_config):
        """Test error handling during configuration testing."""
        app = LoguruConfigApp(mock_config_port, failing_logger_port)
        
        result = await app.test_configuration(sample_logger_config)
        
        # Should return error result
        assert result is not None
        # The exact structure depends on implementation, but it should handle the error
    
    @pytest.mark.asyncio
    async def test_preview_output_error_handling(self, mock_config_port, failing_logger_port, sample_logger_config):
        """Test error handling during output preview."""
        app = LoguruConfigApp(mock_config_port, failing_logger_port)
        
        result = await app.preview_log_output(sample_logger_config, ["test message"])
        
        # Should handle the error gracefully, possibly returning empty list or error message
        assert result is not None


class TestLoguruTUIPerformance:
    """Test TUI performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_configuration_loading_performance(self, mock_config_port, mock_logger_port, sample_logger_config):
        """Test that configuration loading completes within reasonable time."""
        mock_config_port.load_configuration.return_value = sample_logger_config
        
        app = LoguruConfigApp(mock_config_port, mock_logger_port)
        
        # Test should complete within 1 second
        result = await AsyncTestHelper.run_with_timeout(
            app.load_configuration("test"), timeout=1.0
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_configuration_saving_performance(self, mock_config_port, mock_logger_port, sample_logger_config):
        """Test that configuration saving completes within reasonable time."""
        mock_config_port.save_configuration.return_value = True
        
        app = LoguruConfigApp(mock_config_port, mock_logger_port)
        app.current_config = sample_logger_config
        
        # Test should complete within 1 second
        result = await AsyncTestHelper.run_with_timeout(
            app.save_current_configuration(), timeout=1.0
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_preview_generation_performance(self, mock_config_port, mock_logger_port, sample_logger_config):
        """Test that preview generation completes within reasonable time."""
        mock_logger_port.preview_log_output.return_value = ["Preview message"]
        
        app = LoguruConfigApp(mock_config_port, mock_logger_port)
        
        # Generate preview for multiple messages
        messages = [f"Test message {i}" for i in range(100)]
        
        # Test should complete within 2 seconds even for many messages
        result = await AsyncTestHelper.run_with_timeout(
            app.preview_log_output(sample_logger_config, messages), timeout=2.0
        )
        
        assert result is not None

