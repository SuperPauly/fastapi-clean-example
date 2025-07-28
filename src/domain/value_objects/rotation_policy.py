"""Rotation policy value object for Loguru configuration."""

from enum import Enum
from typing import Optional, Union, Dict, Any
from pydantic import BaseModel, Field, field_validator
import re


class RotationType(str, Enum):
    """Types of log rotation."""
    
    SIZE = "size"
    TIME = "time"
    BOTH = "both"
    NONE = "none"


class TimeUnit(str, Enum):
    """Time units for rotation."""
    
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class SizeUnit(str, Enum):
    """Size units for rotation."""
    
    B = "B"
    KB = "KB"
    MB = "MB"
    GB = "GB"
    TB = "TB"


class RotationPolicy(BaseModel):
    """Log rotation policy configuration."""
    
    rotation_type: RotationType = Field(
        default=RotationType.NONE,
        description="Type of rotation to use"
    )
    
    # Size-based rotation
    size_limit: Optional[int] = Field(
        default=None,
        description="Size limit for rotation (in bytes)"
    )
    
    size_unit: SizeUnit = Field(
        default=SizeUnit.MB,
        description="Unit for size limit"
    )
    
    # Time-based rotation
    time_interval: Optional[int] = Field(
        default=None,
        description="Time interval for rotation"
    )
    
    time_unit: TimeUnit = Field(
        default=TimeUnit.DAY,
        description="Unit for time interval"
    )
    
    # Specific time rotation (e.g., "00:00" for daily at midnight)
    rotation_time: Optional[str] = Field(
        default=None,
        description="Specific time for rotation (HH:MM format)"
    )
    
    # Retention policy
    retention_count: Optional[int] = Field(
        default=None,
        description="Number of rotated files to keep"
    )
    
    retention_time: Optional[str] = Field(
        default=None,
        description="Time to keep rotated files (e.g., '7 days', '2 weeks')"
    )
    
    # Compression
    compression: Optional[str] = Field(
        default=None,
        description="Compression format for rotated files (gz, bz2, xz, lzma, tar.gz, tar.bz2, tar.xz)"
    )
    
    @field_validator('size_limit')
    @classmethod
    def validate_size_limit(cls, v: Optional[int]) -> Optional[int]:
        """Validate size limit."""
        if v is not None and v <= 0:
            raise ValueError("Size limit must be positive")
        return v
    
    @field_validator('time_interval')
    @classmethod
    def validate_time_interval(cls, v: Optional[int]) -> Optional[int]:
        """Validate time interval."""
        if v is not None and v <= 0:
            raise ValueError("Time interval must be positive")
        return v
    
    @field_validator('rotation_time')
    @classmethod
    def validate_rotation_time(cls, v: Optional[str]) -> Optional[str]:
        """Validate rotation time format."""
        if v is not None:
            if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', v):
                raise ValueError("Rotation time must be in HH:MM format (24-hour)")
        return v
    
    @field_validator('retention_count')
    @classmethod
    def validate_retention_count(cls, v: Optional[int]) -> Optional[int]:
        """Validate retention count."""
        if v is not None and v < 0:
            raise ValueError("Retention count must be non-negative")
        return v
    
    @field_validator('retention_time')
    @classmethod
    def validate_retention_time(cls, v: Optional[str]) -> Optional[str]:
        """Validate retention time format."""
        if v is not None:
            # Basic validation for time expressions like "7 days", "2 weeks", etc.
            pattern = r'^\d+\s+(second|minute|hour|day|week|month)s?$'
            if not re.match(pattern, v.lower()):
                raise ValueError("Retention time must be in format like '7 days', '2 weeks', etc.")
        return v
    
    @field_validator('compression')
    @classmethod
    def validate_compression(cls, v: Optional[str]) -> Optional[str]:
        """Validate compression format."""
        if v is not None:
            valid_formats = {'gz', 'bz2', 'xz', 'lzma', 'tar.gz', 'tar.bz2', 'tar.xz'}
            if v.lower() not in valid_formats:
                raise ValueError(f"Compression must be one of: {', '.join(valid_formats)}")
        return v.lower() if v else v
    
    @property
    def size_in_bytes(self) -> Optional[int]:
        """Get size limit in bytes."""
        if self.size_limit is None:
            return None
        
        multipliers = {
            SizeUnit.B: 1,
            SizeUnit.KB: 1024,
            SizeUnit.MB: 1024 ** 2,
            SizeUnit.GB: 1024 ** 3,
            SizeUnit.TB: 1024 ** 4,
        }
        
        return self.size_limit * multipliers[self.size_unit]
    
    @property
    def size_display(self) -> Optional[str]:
        """Get human-readable size display."""
        if self.size_limit is None:
            return None
        return f"{self.size_limit} {self.size_unit.value}"
    
    @property
    def time_display(self) -> Optional[str]:
        """Get human-readable time display."""
        if self.time_interval is None:
            return None
        unit = self.time_unit.value
        if self.time_interval != 1:
            unit += "s"
        return f"{self.time_interval} {unit}"
    
    def get_loguru_rotation(self) -> Union[str, int, None]:
        """Get rotation parameter for Loguru."""
        if self.rotation_type == RotationType.NONE:
            return None
        elif self.rotation_type == RotationType.SIZE:
            if self.size_in_bytes is None:
                return None
            return f"{self.size_limit} {self.size_unit.value}"
        elif self.rotation_type == RotationType.TIME:
            if self.rotation_time:
                return self.rotation_time
            elif self.time_interval:
                return f"{self.time_interval} {self.time_unit.value}"
            return None
        elif self.rotation_type == RotationType.BOTH:
            # For both, we'll use size as primary and time as secondary
            # This is a simplified approach - Loguru supports more complex scenarios
            if self.size_in_bytes:
                return f"{self.size_limit} {self.size_unit.value}"
            elif self.rotation_time:
                return self.rotation_time
            elif self.time_interval:
                return f"{self.time_interval} {self.time_unit.value}"
        
        return None
    
    def get_loguru_retention(self) -> Union[str, int, None]:
        """Get retention parameter for Loguru."""
        if self.retention_count is not None:
            return self.retention_count
        elif self.retention_time is not None:
            return self.retention_time
        return None
    
    def get_loguru_compression(self) -> Optional[str]:
        """Get compression parameter for Loguru."""
        return self.compression
    
    def __str__(self) -> str:
        """String representation of rotation policy."""
        if self.rotation_type == RotationType.NONE:
            return "No rotation"
        
        parts = []
        if self.rotation_type in [RotationType.SIZE, RotationType.BOTH] and self.size_display:
            parts.append(f"Size: {self.size_display}")
        if self.rotation_type in [RotationType.TIME, RotationType.BOTH]:
            if self.rotation_time:
                parts.append(f"Time: {self.rotation_time}")
            elif self.time_display:
                parts.append(f"Interval: {self.time_display}")
        
        result = ", ".join(parts) if parts else "Rotation enabled"
        
        if self.retention_count:
            result += f", Keep: {self.retention_count} files"
        elif self.retention_time:
            result += f", Keep: {self.retention_time}"
        
        if self.compression:
            result += f", Compress: {self.compression}"
        
        return result
    
    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
    }
