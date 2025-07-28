"""Mock repository implementations for testing."""

from typing import Optional, List, Dict, Any
from unittest.mock import AsyncMock
from pathlib import Path
import json

from src.application.ports.logger_configuration import LoggerConfigurationPort, LoggerApplicationPort
from src.domain.entities.logger_config import LoggerConfig


class MockLoggerConfigurationRepository:
    """Mock implementation of LoggerConfigurationPort for testing."""
    
    def __init__(self):
        self.configurations: Dict[str, LoggerConfig] = {}
        self.storage_path = Path("/tmp/test_configs")
        self.storage_path.mkdir(exist_ok=True)
    
    async def load_configuration(self, name: Optional[str] = None) -> Optional[LoggerConfig]:
        """Load configuration by name."""
        config_name = name or "default"
        return self.configurations.get(config_name)
    
    async def save_configuration(self, config: LoggerConfig) -> bool:
        """Save configuration."""
        try:
            self.configurations[config.name] = config
            # Simulate file persistence
            config_file = self.storage_path / f"{config.name}.json"
            with open(config_file, 'w') as f:
                json.dump(config.model_dump(), f, indent=2, default=str)
            return True
        except Exception:
            return False
    
    async def delete_configuration(self, name: str) -> bool:
        """Delete configuration by name."""
        try:
            if name in self.configurations:
                del self.configurations[name]
                config_file = self.storage_path / f"{name}.json"
                if config_file.exists():
                    config_file.unlink()
                return True
            return False
        except Exception:
            return False
    
    async def list_configurations(self) -> List[str]:
        """List all configuration names."""
        return list(self.configurations.keys())
    
    async def get_configuration_summary(self, name: str) -> Optional[Dict[str, Any]]:
        """Get configuration summary."""
        config = self.configurations.get(name)
        if not config:
            return None
        
        return {
            "name": config.name,
            "description": config.description,
            "enabled": config.enabled,
            "global_level": str(config.global_level),
            "handlers_count": len(config.handlers),
            "enabled_handlers_count": len([h for h in config.handlers if h.enabled]),
            "has_file_output": any(h.handler_type == "file" for h in config.handlers),
            "has_console_output": any(h.handler_type == "console" for h in config.handlers),
            "warnings": []
        }
    
    async def validate_configuration(self, config: LoggerConfig) -> List[str]:
        """Validate configuration and return warnings."""
        warnings = []
        
        if not config.handlers:
            warnings.append("No handlers configured - logs will not be output anywhere")
        
        if not any(h.enabled for h in config.handlers):
            warnings.append("All handlers are disabled - logs will not be output")
        
        for handler in config.handlers:
            if handler.handler_type == "file" and not handler.sink:
                warnings.append(f"File handler '{handler.name}' has no sink configured")
        
        return warnings
    
    async def export_configuration(self, name: str, format: str = "json") -> Optional[str]:
        """Export configuration to string format."""
        config = self.configurations.get(name)
        if not config:
            return None
        
        if format == "json":
            return json.dumps(config.model_dump(), indent=2, default=str)
        elif format == "yaml":
            # Simulate YAML export
            return f"# YAML export of {name}\nname: {config.name}\nenabled: {config.enabled}"
        elif format == "toml":
            # Simulate TOML export
            return f"# TOML export of {name}\nname = \"{config.name}\"\nenabled = {config.enabled}"
        
        return None
    
    async def import_configuration(self, config_data: str, format: str = "json", name: Optional[str] = None) -> Optional[LoggerConfig]:
        """Import configuration from string format."""
        try:
            if format == "json":
                data = json.loads(config_data)
                # Create a basic LoggerConfig from the data
                config = LoggerConfig(
                    name=name or data.get("name", "imported"),
                    description=data.get("description", "Imported configuration"),
                    enabled=data.get("enabled", True),
                    global_level=data.get("global_level", "INFO"),
                    handlers=data.get("handlers", []),
                    activation=data.get("activation", []),
                    patcher=data.get("patcher"),
                    extra=data.get("extra", {})
                )
                return config
        except Exception:
            pass
        
        return None


class MockLoggerApplicationAdapter:
    """Mock implementation of LoggerApplicationPort for testing."""
    
    def __init__(self):
        self.current_config: Optional[LoggerConfig] = None
        self.applied_configs: List[LoggerConfig] = []
        self.test_results: Dict[str, Any] = {}
    
    async def apply_configuration(self, config: LoggerConfig) -> bool:
        """Apply configuration to logger."""
        try:
            self.current_config = config
            self.applied_configs.append(config)
            return True
        except Exception:
            return False
    
    async def test_configuration(self, config: LoggerConfig, test_messages: Optional[List[str]] = None) -> Dict[str, Any]:
        """Test configuration with sample messages."""
        messages = test_messages or [
            "Test DEBUG message",
            "Test INFO message", 
            "Test WARNING message",
            "Test ERROR message"
        ]
        
        return {
            "success": True,
            "config_name": config.name,
            "messages_tested": len(messages),
            "output": [f"[{config.global_level}] {msg}" for msg in messages],
            "errors": [],
            "warnings": [],
            "performance": {
                "execution_time": 0.001,
                "memory_usage": "1.2MB"
            }
        }
    
    async def get_current_configuration(self) -> Optional[LoggerConfig]:
        """Get currently active configuration."""
        return self.current_config
    
    async def reset_logger(self) -> bool:
        """Reset logger to default state."""
        try:
            self.current_config = None
            return True
        except Exception:
            return False
    
    async def preview_log_output(self, config: LoggerConfig, sample_messages: List[str]) -> List[str]:
        """Preview log output with given configuration."""
        formatted_messages = []
        
        for message in sample_messages:
            # Simulate formatted output based on configuration
            if config.handlers:
                handler = config.handlers[0]  # Use first handler for preview
                if handler.format_config.preset.value == "simple":
                    formatted = f"{config.global_level.value} | {message}"
                elif handler.format_config.preset.value == "detailed":
                    formatted = f"2024-01-01 12:00:00.000 | {config.global_level.value} | module:function:123 | {message}"
                elif handler.format_config.preset.value == "json":
                    formatted = f'{{"timestamp": "2024-01-01T12:00:00", "level": "{config.global_level.value}", "message": "{message}"}}'
                else:
                    formatted = f"{config.global_level.value} | {message}"
            else:
                formatted = f"{config.global_level.value} | {message}"
            
            formatted_messages.append(formatted)
        
        return formatted_messages

