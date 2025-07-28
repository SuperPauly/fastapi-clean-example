"""Logger configuration entity for Loguru."""

from typing import Optional, List, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
from uuid import UUID, uuid4

from src.domain.value_objects.log_level import LogLevel, LogLevelEnum
from src.domain.value_objects.log_format import LogFormat, LogFormatPreset
from src.domain.value_objects.rotation_policy import RotationPolicy, RotationType


class HandlerConfig(BaseModel):
    """Configuration for a single log handler."""
    
    id: UUID = Field(default_factory=uuid4, description="Unique handler ID")
    name: str = Field(..., description="Handler name")
    enabled: bool = Field(default=True, description="Whether handler is enabled")
    
    # Handler type and sink
    handler_type: str = Field(default="console", description="Type of handler (console, file, syslog, systemd)")
    sink: Optional[str] = Field(default=None, description="Handler sink (file path, etc.)")
    
    # Logging configuration
    level: LogLevel = Field(default_factory=lambda: LogLevel(value=LogLevelEnum.INFO))
    format_config: LogFormat = Field(default_factory=LogFormat)
    rotation: RotationPolicy = Field(default_factory=RotationPolicy)
    
    # Handler-specific options
    enqueue: bool = Field(default=False, description="Enable async logging")
    catch: bool = Field(default=True, description="Catch exceptions in handler")
    
    # File-specific options
    encoding: str = Field(default="utf-8", description="File encoding")
    mode: str = Field(default="a", description="File open mode")
    buffering: int = Field(default=1, description="File buffering")
    
    # Filter function (as string for serialization)
    filter_expression: Optional[str] = Field(default=None, description="Filter expression")
    
    @field_validator('handler_type')
    @classmethod
    def validate_handler_type(cls, v: str) -> str:
        """Validate handler type."""
        valid_types = {'console', 'file', 'syslog', 'systemd', 'stderr', 'stdout'}
        if v.lower() not in valid_types:
            raise ValueError(f"Handler type must be one of: {', '.join(valid_types)}")
        return v.lower()
    
    @field_validator('sink')
    @classmethod
    def validate_sink(cls, v: Optional[str], info) -> Optional[str]:
        """Validate sink based on handler type."""
        if v is None:
            return v
        
        handler_type = info.data.get('handler_type', 'console')
        
        if handler_type == 'file':
            # Validate file path
            try:
                path = Path(v)
                # Create parent directories if they don't exist
                path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ValueError(f"Invalid file path: {e}")
        
        return v
    
    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v: str) -> str:
        """Validate file mode."""
        valid_modes = {'a', 'w', 'x'}
        if v not in valid_modes:
            raise ValueError(f"File mode must be one of: {', '.join(valid_modes)}")
        return v
    
    def get_loguru_config(self) -> Dict[str, Any]:
        """Get configuration dict for Loguru add() method."""
        config = {
            "level": str(self.level.value),
            "enqueue": self.enqueue,
            "catch": self.catch,
        }
        
        # Add format configuration
        config.update(self.format_config.get_loguru_config())
        
        # Add rotation configuration
        rotation = self.rotation.get_loguru_rotation()
        if rotation is not None:
            config["rotation"] = rotation
        
        retention = self.rotation.get_loguru_retention()
        if retention is not None:
            config["retention"] = retention
        
        compression = self.rotation.get_loguru_compression()
        if compression is not None:
            config["compression"] = compression
        
        # Add handler-specific configuration
        if self.handler_type == 'file':
            config.update({
                "encoding": self.encoding,
                "mode": self.mode,
                "buffering": self.buffering,
            })
        
        # Add filter if specified
        if self.filter_expression:
            # Note: In a real implementation, you'd want to parse and compile the filter
            # For now, we'll store it as a string
            config["filter"] = self.filter_expression
        
        return config
    
    @property
    def display_name(self) -> str:
        """Get display name for the handler."""
        if self.handler_type == 'file' and self.sink:
            return f"{self.name} ({Path(self.sink).name})"
        return f"{self.name} ({self.handler_type})"
    
    def __str__(self) -> str:
        """String representation of handler config."""
        status = "enabled" if self.enabled else "disabled"
        return f"{self.display_name} - {status}"


class LoggerConfig(BaseModel):
    """Complete logger configuration entity."""
    
    id: UUID = Field(default_factory=uuid4, description="Unique configuration ID")
    name: str = Field(default="default", description="Configuration name")
    description: Optional[str] = Field(default=None, description="Configuration description")
    
    # Global settings
    enabled: bool = Field(default=True, description="Whether logging is enabled")
    global_level: LogLevel = Field(default_factory=lambda: LogLevel(value=LogLevelEnum.INFO))
    
    # Handlers
    handlers: List[HandlerConfig] = Field(default_factory=list, description="List of log handlers")
    
    # Global options
    activation: List[str] = Field(default_factory=list, description="Modules to activate logging for")
    
    # Advanced options
    patcher: Optional[str] = Field(default=None, description="Patcher function")
    extra: Dict[str, Any] = Field(default_factory=dict, description="Extra context variables")
    
    @field_validator('handlers')
    @classmethod
    def validate_handlers(cls, v: List[HandlerConfig]) -> List[HandlerConfig]:
        """Validate handlers list."""
        if not v:
            # Add default console handler if no handlers specified
            return [HandlerConfig(
                name="console",
                handler_type="console",
                sink=None
            )]
        
        # Check for duplicate handler names
        names = [h.name for h in v]
        if len(names) != len(set(names)):
            raise ValueError("Handler names must be unique")
        
        return v
    
    def add_handler(self, handler: HandlerConfig) -> None:
        """Add a new handler to the configuration."""
        # Check for duplicate names
        if any(h.name == handler.name for h in self.handlers):
            raise ValueError(f"Handler with name '{handler.name}' already exists")
        
        # Create a new list with the added handler (for immutability)
        new_handlers = self.handlers + [handler]
        object.__setattr__(self, 'handlers', new_handlers)
    
    def remove_handler(self, handler_id: UUID) -> None:
        """Remove a handler from the configuration."""
        new_handlers = [h for h in self.handlers if h.id != handler_id]
        if len(new_handlers) == len(self.handlers):
            raise ValueError(f"Handler with ID '{handler_id}' not found")
        
        object.__setattr__(self, 'handlers', new_handlers)
    
    def get_handler(self, handler_id: UUID) -> Optional[HandlerConfig]:
        """Get a handler by ID."""
        return next((h for h in self.handlers if h.id == handler_id), None)
    
    def get_handler_by_name(self, name: str) -> Optional[HandlerConfig]:
        """Get a handler by name."""
        return next((h for h in self.handlers if h.name == name), None)
    
    @property
    def enabled_handlers(self) -> List[HandlerConfig]:
        """Get list of enabled handlers."""
        return [h for h in self.handlers if h.enabled]
    
    @property
    def has_file_handlers(self) -> bool:
        """Check if configuration has any file handlers."""
        return any(h.handler_type == 'file' for h in self.enabled_handlers)
    
    @property
    def has_console_handlers(self) -> bool:
        """Check if configuration has any console handlers."""
        return any(h.handler_type in ['console', 'stdout', 'stderr'] for h in self.enabled_handlers)
    
    def validate_configuration(self) -> List[str]:
        """Validate the complete configuration and return any warnings."""
        warnings = []
        
        if not self.enabled:
            warnings.append("Logging is disabled")
        
        if not self.enabled_handlers:
            warnings.append("No enabled handlers - logs will not be output")
        
        # Check for file handler issues
        for handler in self.enabled_handlers:
            if handler.handler_type == 'file':
                if not handler.sink:
                    warnings.append(f"File handler '{handler.name}' has no sink specified")
                else:
                    try:
                        path = Path(handler.sink)
                        if not path.parent.exists():
                            warnings.append(f"Directory for '{handler.sink}' does not exist")
                    except Exception:
                        warnings.append(f"Invalid file path for handler '{handler.name}'")
        
        return warnings
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the configuration."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "global_level": str(self.global_level),
            "handlers_count": len(self.handlers),
            "enabled_handlers_count": len(self.enabled_handlers),
            "has_file_output": self.has_file_handlers,
            "has_console_output": self.has_console_handlers,
            "warnings": self.validate_configuration(),
        }
    
    def __str__(self) -> str:
        """String representation of logger config."""
        status = "enabled" if self.enabled else "disabled"
        handler_count = len(self.enabled_handlers)
        return f"{self.name} - {status} ({handler_count} handlers)"
    
    model_config = {
        "frozen": True,
        "arbitrary_types_allowed": True,
    }
