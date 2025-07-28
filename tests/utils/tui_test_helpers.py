"""Test utilities for TUI testing."""

import asyncio
from typing import Any, Dict, List, Optional, Callable
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import tempfile
import json

from textual.app import App
from textual.widgets import Widget


class TUITestHelper:
    """Helper class for TUI testing operations."""
    
    @staticmethod
    async def simulate_key_press(app: App, key: str, widget: Optional[Widget] = None):
        """Simulate a key press in the TUI."""
        # This would be implemented with actual Textual testing utilities
        # For now, we'll create a mock implementation
        if hasattr(app, '_handle_key'):
            await app._handle_key(key, widget)
    
    @staticmethod
    async def simulate_button_click(app: App, button_id: str):
        """Simulate a button click in the TUI."""
        button = app.query_one(f"#{button_id}")
        if button and hasattr(button, 'press'):
            await button.press()
    
    @staticmethod
    async def get_widget_text(app: App, widget_id: str) -> str:
        """Get text content from a widget."""
        try:
            widget = app.query_one(f"#{widget_id}")
            if hasattr(widget, 'renderable'):
                return str(widget.renderable)
            elif hasattr(widget, 'text'):
                return widget.text
            return ""
        except Exception:
            return ""
    
    @staticmethod
    async def wait_for_widget(app: App, widget_id: str, timeout: float = 5.0) -> bool:
        """Wait for a widget to appear in the TUI."""
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                app.query_one(f"#{widget_id}")
                return True
            except Exception:
                await asyncio.sleep(0.1)
        return False
    
    @staticmethod
    async def simulate_navigation(app: App, navigation_steps: List[str]):
        """Simulate navigation through TUI sections."""
        for step in navigation_steps:
            if step.startswith("key:"):
                key = step[4:]
                await TUITestHelper.simulate_key_press(app, key)
            elif step.startswith("click:"):
                button_id = step[6:]
                await TUITestHelper.simulate_button_click(app, button_id)
            await asyncio.sleep(0.1)  # Small delay between actions
    
    @staticmethod
    def create_mock_app_with_widgets(widget_configs: List[Dict[str, Any]]) -> Mock:
        """Create a mock app with specified widgets."""
        mock_app = Mock()
        mock_widgets = {}
        
        for config in widget_configs:
            widget_id = config.get('id')
            widget_type = config.get('type', 'Widget')
            widget_props = config.get('props', {})
            
            mock_widget = Mock()
            mock_widget.id = widget_id
            mock_widget.type = widget_type
            
            for prop, value in widget_props.items():
                setattr(mock_widget, prop, value)
            
            mock_widgets[widget_id] = mock_widget
        
        def mock_query_one(selector: str):
            # Extract ID from selector (e.g., "#button_id" -> "button_id")
            widget_id = selector.lstrip('#')
            if widget_id in mock_widgets:
                return mock_widgets[widget_id]
            raise Exception(f"Widget {selector} not found")
        
        mock_app.query_one = mock_query_one
        mock_app.query = Mock(return_value=list(mock_widgets.values()))
        
        return mock_app


class ConfigurationTestHelper:
    """Helper class for configuration-related testing."""
    
    @staticmethod
    def create_test_config_data(name: str = "test", **overrides) -> Dict[str, Any]:
        """Create test configuration data."""
        default_config = {
            "name": name,
            "description": f"Test configuration {name}",
            "enabled": True,
            "global_level": {"value": "DEBUG"},
            "handlers": [
                {
                    "id": "test-handler-1",
                    "name": "console",
                    "enabled": True,
                    "handler_type": "console",
                    "sink": "sys.stdout",
                    "level": {"value": "INFO"},
                    "format_config": {
                        "preset": "simple",
                        "custom_format": None,
                        "colorize": True,
                        "serialize": False,
                        "backtrace": True,
                        "diagnose": True
                    },
                    "rotation": {
                        "rotation_type": "none",
                        "size_limit": None,
                        "size_unit": "MB",
                        "time_interval": None,
                        "time_unit": "day",
                        "rotation_time": None,
                        "retention_count": None,
                        "retention_time": None,
                        "compression": None
                    },
                    "enqueue": False,
                    "catch": True,
                    "encoding": "utf-8",
                    "mode": "a",
                    "buffering": 1,
                    "filter_expression": None
                }
            ],
            "activation": [],
            "patcher": None,
            "extra": {}
        }
        
        # Apply overrides
        for key, value in overrides.items():
            if '.' in key:
                # Handle nested keys like "handlers.0.enabled"
                keys = key.split('.')
                current = default_config
                for k in keys[:-1]:
                    if k.isdigit():
                        current = current[int(k)]
                    else:
                        current = current[k]
                current[keys[-1]] = value
            else:
                default_config[key] = value
        
        return default_config
    
    @staticmethod
    def create_temp_config_file(config_data: Dict[str, Any], filename: str = "test_config.json") -> Path:
        """Create a temporary configuration file."""
        temp_dir = Path(tempfile.mkdtemp())
        config_file = temp_dir / filename
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        return config_file
    
    @staticmethod
    def validate_config_structure(config_data: Dict[str, Any]) -> List[str]:
        """Validate configuration structure and return any issues."""
        issues = []
        
        required_fields = ["name", "enabled", "global_level", "handlers"]
        for field in required_fields:
            if field not in config_data:
                issues.append(f"Missing required field: {field}")
        
        if "handlers" in config_data:
            for i, handler in enumerate(config_data["handlers"]):
                if not isinstance(handler, dict):
                    issues.append(f"Handler {i} is not a dictionary")
                    continue
                
                required_handler_fields = ["name", "enabled", "handler_type"]
                for field in required_handler_fields:
                    if field not in handler:
                        issues.append(f"Handler {i} missing required field: {field}")
        
        return issues


class AsyncTestHelper:
    """Helper class for async testing operations."""
    
    @staticmethod
    async def run_with_timeout(coro, timeout: float = 5.0):
        """Run an async operation with timeout."""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            raise AssertionError(f"Operation timed out after {timeout} seconds")
    
    @staticmethod
    def create_async_mock(return_value=None, side_effect=None) -> AsyncMock:
        """Create an AsyncMock with specified behavior."""
        mock = AsyncMock()
        if return_value is not None:
            mock.return_value = return_value
        if side_effect is not None:
            mock.side_effect = side_effect
        return mock
    
    @staticmethod
    async def simulate_async_delay(delay: float = 0.1):
        """Simulate async delay for testing timing-dependent operations."""
        await asyncio.sleep(delay)


class FileSystemTestHelper:
    """Helper class for file system testing operations."""
    
    @staticmethod
    def create_temp_directory_structure(structure: Dict[str, Any]) -> Path:
        """Create a temporary directory structure for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        
        def create_structure(base_path: Path, struct: Dict[str, Any]):
            for name, content in struct.items():
                path = base_path / name
                if isinstance(content, dict):
                    path.mkdir(exist_ok=True)
                    create_structure(path, content)
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    if isinstance(content, str):
                        path.write_text(content)
                    elif isinstance(content, bytes):
                        path.write_bytes(content)
                    else:
                        path.write_text(str(content))
        
        create_structure(temp_dir, structure)
        return temp_dir
    
    @staticmethod
    def cleanup_temp_directory(temp_dir: Path):
        """Clean up temporary directory after testing."""
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


class MockingHelper:
    """Helper class for creating mocks and patches."""
    
    @staticmethod
    def patch_textual_app(app_class):
        """Create a patch for a Textual app class."""
        return patch.object(app_class, 'run_async', new_callable=AsyncMock)
    
    @staticmethod
    def patch_file_operations():
        """Create patches for file operations."""
        return {
            'open': patch('builtins.open'),
            'path_exists': patch('pathlib.Path.exists'),
            'path_mkdir': patch('pathlib.Path.mkdir'),
            'path_write_text': patch('pathlib.Path.write_text'),
            'path_read_text': patch('pathlib.Path.read_text')
        }
    
    @staticmethod
    def create_mock_dependencies():
        """Create a set of mock dependencies for testing."""
        return {
            'config_port': Mock(),
            'logger_port': Mock(),
            'settings': Mock(),
            'file_system': Mock()
        }

