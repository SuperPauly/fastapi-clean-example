"""Log format value object for Loguru configuration."""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class LogFormatPreset(str, Enum):
    """Predefined log format presets."""
    
    SIMPLE = "simple"
    DETAILED = "detailed"
    JSON = "json"
    COMPACT = "compact"
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    CUSTOM = "custom"


class LogFormat(BaseModel):
    """Log format value object with validation and presets."""
    
    preset: LogFormatPreset = Field(
        default=LogFormatPreset.SIMPLE,
        description="Predefined format preset"
    )
    
    custom_format: Optional[str] = Field(
        default=None,
        description="Custom format string when preset is CUSTOM"
    )
    
    colorize: bool = Field(
        default=True,
        description="Enable colorized output"
    )
    
    serialize: bool = Field(
        default=False,
        description="Serialize logs as JSON"
    )
    
    backtrace: bool = Field(
        default=True,
        description="Enable backtrace in error logs"
    )
    
    diagnose: bool = Field(
        default=True,
        description="Enable variable values in backtrace"
    )
    
    @field_validator('custom_format')
    @classmethod
    def validate_custom_format(cls, v: Optional[str], info) -> Optional[str]:
        """Validate custom format string."""
        if v is not None:
            if not v.strip():
                raise ValueError("Custom format cannot be empty")
            # Basic validation for Loguru format tokens
            required_tokens = ['{time}', '{level}', '{message}']
            if not any(token in v for token in ['{time}', '{level}', '{message}']):
                raise ValueError("Custom format should contain at least one of: {time}, {level}, {message}")
        return v
    
    @property
    def format_string(self) -> str:
        """Get the actual format string to use."""
        if self.preset == LogFormatPreset.CUSTOM:
            if not self.custom_format:
                raise ValueError("Custom format string is required when preset is CUSTOM")
            return self.custom_format
        
        # Return predefined format strings
        formats = {
            LogFormatPreset.SIMPLE: "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            LogFormatPreset.DETAILED: "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            LogFormatPreset.JSON: None,  # JSON serialization handled separately
            LogFormatPreset.COMPACT: "{time:HH:mm:ss} {level} {message}",
            LogFormatPreset.DEVELOPMENT: "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
            LogFormatPreset.PRODUCTION: "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {process.id} | {thread.id} | {name}:{function}:{line} | {message}",
        }
        
        return formats.get(self.preset, formats[LogFormatPreset.SIMPLE])
    
    @property
    def is_json_format(self) -> bool:
        """Check if this format uses JSON serialization."""
        return self.preset == LogFormatPreset.JSON or self.serialize
    
    @property
    def supports_colors(self) -> bool:
        """Check if this format supports colors."""
        return self.colorize and not self.is_json_format
    
    def get_loguru_config(self) -> Dict[str, Any]:
        """Get configuration dict for Loguru handler."""
        config = {
            "colorize": self.supports_colors,
            "serialize": self.is_json_format,
            "backtrace": self.backtrace,
            "diagnose": self.diagnose,
        }
        
        if not self.is_json_format:
            config["format"] = self.format_string
        
        return config
    
    def __str__(self) -> str:
        """String representation of log format."""
        if self.preset == LogFormatPreset.CUSTOM:
            return f"Custom: {self.custom_format}"
        return f"Preset: {self.preset.value}"
    
    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
    }
