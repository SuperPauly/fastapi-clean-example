"""Test fixtures for TUI testing."""

import pytest
from unittest.mock import AsyncMock, Mock
from pathlib import Path
from typing import Dict, Any, List, Optional
import tempfile
import json

from src.domain.entities.logger_config import LoggerConfig
from src.domain.value_objects.log_level import LogLevel
from src.domain.value_objects.log_format import LogFormat, FormatPreset
from src.domain.value_objects.rotation_policy import RotationPolicy, RotationType
from src.application.ports.logger_configuration import LoggerConfigurationPort, LoggerApplicationPort


@pytest.fixture
def sample_logger_config() -> LoggerConfig:
    """Create a sample logger configuration for testing."""
    return LoggerConfig(
        name="test_config",
        description="Test configuration",
        enabled=True,
        global_level=LogLevel.DEBUG,
        handlers=[],
        activation=[],
        patcher=None,
        extra={}
    )


@pytest.fixture
def sample_log_format() -> LogFormat:
    """Create a sample log format for testing."""
    return LogFormat(
        preset=FormatPreset.SIMPLE,
        custom_format=None,
        colorize=True,
        serialize=False,
        backtrace=True,
        diagnose=True
    )


@pytest.fixture
def sample_rotation_policy() -> RotationPolicy:
    """Create a sample rotation policy for testing."""
    return RotationPolicy(
        rotation_type=RotationType.SIZE,
        size_limit=10,
        size_unit="MB",
        time_interval=None,
        time_unit="day",
        rotation_time=None,
        retention_count=5,
        retention_time=None,
        compression=None
    )


@pytest.fixture
def mock_config_port() -> Mock:
    """Create a mock configuration port for testing."""
    mock = Mock(spec=LoggerConfigurationPort)
    mock.load_configuration = AsyncMock(return_value=None)
    mock.save_configuration = AsyncMock(return_value=True)
    mock.delete_configuration = AsyncMock(return_value=True)
    mock.list_configurations = AsyncMock(return_value=["default", "test"])
    mock.get_configuration_summary = AsyncMock(return_value={
        "name": "test",
        "enabled": True,
        "handlers_count": 1,
        "warnings": []
    })
    mock.validate_configuration = AsyncMock(return_value=[])
    mock.export_configuration = AsyncMock(return_value='{"test": "config"}')
    mock.import_configuration = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def mock_logger_port() -> Mock:
    """Create a mock logger application port for testing."""
    mock = Mock(spec=LoggerApplicationPort)
    mock.apply_configuration = AsyncMock(return_value=True)
    mock.test_configuration = AsyncMock(return_value={
        "success": True,
        "output": ["Test log message"],
        "errors": []
    })
    mock.get_current_configuration = AsyncMock(return_value=None)
    mock.reset_logger = AsyncMock(return_value=True)
    mock.preview_log_output = AsyncMock(return_value=[
        "2024-01-01 12:00:00 | INFO | Test message"
    ])
    return mock


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for configuration files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "configs" / "logging"
        config_dir.mkdir(parents=True, exist_ok=True)
        yield config_dir


@pytest.fixture
def sample_config_file(temp_config_dir):
    """Create a sample configuration file for testing."""
    config_data = {
        "name": "test_config",
        "description": "Test configuration",
        "enabled": True,
        "global_level": {"value": "DEBUG"},
        "handlers": [],
        "activation": [],
        "patcher": None,
        "extra": {}
    }
    
    config_file = temp_config_dir / "test_config.json"
    with open(config_file, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    return config_file


@pytest.fixture
def mock_dynaconf_settings():
    """Create mock Dynaconf settings for testing."""
    mock = Mock()
    mock.get = Mock(return_value=None)
    mock.set = Mock()
    mock.save = Mock()
    mock.load_file = Mock()
    mock.to_dict = Mock(return_value={})
    return mock


@pytest.fixture
def tui_test_data():
    """Provide test data for TUI interactions."""
    return {
        "navigation_items": [
            "Basic Settings",
            "File Configuration", 
            "Formatting & Colors",
            "Rotation & Retention",
            "Handlers & Output",
            "Advanced Options",
            "Test Configuration",
            "Save/Load Configuration"
        ],
        "log_levels": ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"],
        "format_presets": ["simple", "detailed", "json", "compact", "development", "production"],
        "rotation_types": ["none", "size", "time", "both"],
        "sample_messages": [
            "This is a test debug message",
            "This is a test info message", 
            "This is a test warning message",
            "This is a test error message"
        ]
    }


@pytest.fixture
def mock_textual_app():
    """Create a mock Textual app for testing."""
    mock = Mock()
    mock.push_screen = AsyncMock()
    mock.pop_screen = AsyncMock()
    mock.exit = AsyncMock()
    mock.query = Mock()
    mock.query_one = Mock()
    return mock


@pytest.fixture
def keyboard_events():
    """Provide keyboard event data for testing."""
    return {
        "enter": {"key": "enter"},
        "escape": {"key": "escape"},
        "tab": {"key": "tab"},
        "up": {"key": "up"},
        "down": {"key": "down"},
        "left": {"key": "left"},
        "right": {"key": "right"},
        "space": {"key": "space"},
        "ctrl_c": {"key": "ctrl+c"},
        "ctrl_s": {"key": "ctrl+s"}
    }


@pytest.fixture
def async_test_timeout():
    """Provide timeout settings for async tests."""
    return 5.0  # 5 seconds timeout for async operations

