"""Log level value object for Loguru configuration."""

from enum import Enum
from typing import Union
from pydantic import BaseModel, Field, field_validator


class LogLevelEnum(str, Enum):
    """Supported log levels in Loguru."""
    
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogLevel(BaseModel):
    """Log level value object with validation."""
    
    value: Union[LogLevelEnum, str, int] = Field(
        default=LogLevelEnum.INFO,
        description="Log level - can be enum, string, or numeric"
    )
    
    @field_validator('value')
    @classmethod
    def validate_log_level(cls, v: Union[LogLevelEnum, str, int]) -> Union[LogLevelEnum, str, int]:
        """Validate log level value."""
        if isinstance(v, LogLevelEnum):
            return v
        elif isinstance(v, str):
            # Try to convert to enum first
            try:
                return LogLevelEnum(v.upper())
            except ValueError:
                # Allow custom string levels (Loguru supports this)
                if v.strip():
                    return v.upper()
                raise ValueError("Log level string cannot be empty")
        elif isinstance(v, int):
            # Loguru supports numeric levels
            if v < 0:
                raise ValueError("Numeric log level must be non-negative")
            return v
        else:
            raise ValueError("Log level must be string, enum, or integer")
    
    @property
    def is_standard(self) -> bool:
        """Check if this is a standard Loguru log level."""
        return isinstance(self.value, LogLevelEnum)
    
    @property
    def is_custom(self) -> bool:
        """Check if this is a custom log level."""
        return isinstance(self.value, str) and not self.is_standard
    
    @property
    def is_numeric(self) -> bool:
        """Check if this is a numeric log level."""
        return isinstance(self.value, int)
    
    def __str__(self) -> str:
        """String representation of log level."""
        return str(self.value)
    
    def __eq__(self, other) -> bool:
        """Compare log levels."""
        if isinstance(other, LogLevel):
            return self.value == other.value
        return self.value == other
    
    def __hash__(self) -> int:
        """Hash for log level."""
        return hash(self.value)
    
    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
    }
