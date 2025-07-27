"""Loguru integration adapter for applying configuration to actual logger."""

import asyncio
import sys
import io
from typing import Optional, List, Dict, Any
from contextlib import redirect_stdout, redirect_stderr
try:
    from loguru import logger
except ImportError:
    # Mock logger for testing when loguru is not available
    class MockLogger:
        def add(self, sink, **kwargs):
            return 1
        def remove(self, handler_id=None):
            pass
        def log(self, level, message):
            print(f"[MOCK] {level}: {message}")
    
    logger = MockLogger()

from src.application.ports.logger_configuration import LoggerApplicationPort
from src.domain.entities.logger_config import LoggerConfig


class LoguruConfigAdapter(LoggerApplicationPort):
    """Loguru implementation of logger application port."""
    
    def __init__(self):
        """Initialize the Loguru adapter."""
        self._current_config: Optional[LoggerConfig] = None
        self._handler_ids: List[int] = []
    
    async def apply_configuration(self, config: LoggerConfig) -> bool:
        """Apply configuration to the actual logger."""
        try:
            # Remove existing handlers
            await self._clear_handlers()
            
            if not config.enabled:
                # If logging is disabled, don't add any handlers
                self._current_config = config
                return True
            
            # Add new handlers based on configuration
            for handler_config in config.enabled_handlers:
                handler_id = await self._add_handler(handler_config)
                if handler_id is not None:
                    self._handler_ids.append(handler_id)
            
            # Store current configuration
            self._current_config = config
            
            return True
            
        except Exception as e:
            print(f"Error applying configuration: {e}")
            return False
    
    async def test_configuration(
        self, 
        config: LoggerConfig, 
        test_messages: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Test a configuration by applying it temporarily and generating test logs."""
        try:
            # Save current state
            original_config = self._current_config
            original_handler_ids = self._handler_ids.copy()
            
            # Apply test configuration
            success = await self.apply_configuration(config)
            if not success:
                return {
                    "success": False,
                    "error": "Failed to apply test configuration"
                }
            
            # Generate test messages
            if not test_messages:
                test_messages = [
                    "TRACE: This is a trace message for debugging",
                    "DEBUG: Debug information about application state", 
                    "INFO: Application started successfully",
                    "SUCCESS: Operation completed successfully",
                    "WARNING: This is a warning message",
                    "ERROR: An error occurred during processing",
                    "CRITICAL: Critical system failure detected"
                ]
            
            # Capture output for testing
            captured_output = []
            handlers_tested = len(config.enabled_handlers)
            messages_logged = 0
            
            # Log test messages
            for message in test_messages:
                try:
                    # Parse level and message
                    if ": " in message:
                        level_str, msg = message.split(": ", 1)
                        level = level_str.strip()
                    else:
                        level = "INFO"
                        msg = message
                    
                    # Log the message
                    logger.log(level, msg)
                    messages_logged += 1
                    
                except Exception as e:
                    print(f"Error logging test message: {e}")
            
            # Restore original configuration if it existed
            if original_config:
                await self._restore_handlers(original_handler_ids)
                await self.apply_configuration(original_config)
            else:
                await self._clear_handlers()
            
            return {
                "success": True,
                "handlers_tested": handlers_tested,
                "messages_logged": messages_logged,
                "captured_output": captured_output
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_current_configuration(self) -> Optional[LoggerConfig]:
        """Get the currently active logger configuration."""
        return self._current_config
    
    async def reset_logger(self) -> bool:
        """Reset logger to default state."""
        try:
            await self._clear_handlers()
            self._current_config = None
            
            # Add default console handler
            logger.add(sys.stderr, level="INFO")
            
            return True
            
        except Exception as e:
            print(f"Error resetting logger: {e}")
            return False
    
    async def preview_log_output(
        self, 
        config: LoggerConfig, 
        sample_messages: List[str]
    ) -> List[str]:
        """Preview what log output would look like with given configuration."""
        try:
            preview_output = []
            
            for handler_config in config.enabled_handlers:
                if not handler_config.enabled:
                    continue
                
                # Get format configuration
                format_config = handler_config.format_config.get_loguru_config()
                format_string = format_config.get("format", "{time} | {level} | {message}")
                
                # Generate preview for each message
                for message in sample_messages:
                    try:
                        # Parse level and message
                        if ": " in message:
                            level_str, msg = message.split(": ", 1)
                            level = level_str.strip()
                        else:
                            level = "INFO"
                            msg = message
                        
                        # Create a mock log record for preview
                        preview_line = self._format_preview_message(
                            format_string, 
                            level, 
                            msg, 
                            handler_config
                        )
                        
                        if preview_line:
                            preview_output.append(f"[{handler_config.name}] {preview_line}")
                            
                    except Exception as e:
                        preview_output.append(f"[{handler_config.name}] Error formatting message: {e}")
            
            return preview_output
            
        except Exception as e:
            return [f"Error generating preview: {e}"]
    
    async def _clear_handlers(self) -> None:
        """Clear all current handlers."""
        try:
            # Remove all handlers
            logger.remove()
            self._handler_ids.clear()
            
        except Exception as e:
            print(f"Error clearing handlers: {e}")
    
    async def _restore_handlers(self, handler_ids: List[int]) -> None:
        """Restore specific handlers by ID."""
        # Note: Loguru doesn't support restoring handlers by ID after removal
        # This is a limitation we'll document
        pass
    
    async def _add_handler(self, handler_config) -> Optional[int]:
        """Add a single handler based on configuration."""
        try:
            # Get Loguru configuration
            loguru_config = handler_config.get_loguru_config()
            
            # Determine sink based on handler type
            if handler_config.handler_type == "console":
                sink = sys.stderr
            elif handler_config.handler_type == "stdout":
                sink = sys.stdout
            elif handler_config.handler_type == "stderr":
                sink = sys.stderr
            elif handler_config.handler_type == "file":
                if not handler_config.sink:
                    print(f"File handler '{handler_config.name}' has no sink specified")
                    return None
                sink = handler_config.sink
            elif handler_config.handler_type == "syslog":
                # For syslog, we'd need additional configuration
                print(f"Syslog handler not yet implemented")
                return None
            elif handler_config.handler_type == "systemd":
                # For systemd journal, we'd need additional configuration
                print(f"Systemd journal handler not yet implemented")
                return None
            else:
                print(f"Unknown handler type: {handler_config.handler_type}")
                return None
            
            # Add handler to logger
            handler_id = logger.add(sink, **loguru_config)
            
            return handler_id
            
        except Exception as e:
            print(f"Error adding handler '{handler_config.name}': {e}")
            return None
    
    def _format_preview_message(
        self, 
        format_string: str, 
        level: str, 
        message: str, 
        handler_config
    ) -> str:
        """Format a preview message using the format string."""
        try:
            # Simple format string replacement for preview
            # In a real implementation, you'd want to use Loguru's actual formatting
            import datetime
            
            now = datetime.datetime.now()
            
            # Basic replacements
            preview = format_string
            preview = preview.replace("{time}", now.strftime("%Y-%m-%d %H:%M:%S"))
            preview = preview.replace("{time:YYYY-MM-DD HH:mm:ss}", now.strftime("%Y-%m-%d %H:%M:%S"))
            preview = preview.replace("{time:YYYY-MM-DD HH:mm:ss.SSS}", now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
            preview = preview.replace("{time:HH:mm:ss}", now.strftime("%H:%M:%S"))
            preview = preview.replace("{level}", level)
            preview = preview.replace("{level: <8}", f"{level: <8}")
            preview = preview.replace("{message}", message)
            preview = preview.replace("{name}", "preview")
            preview = preview.replace("{function}", "test_function")
            preview = preview.replace("{line}", "42")
            preview = preview.replace("{process.id}", "12345")
            preview = preview.replace("{thread.id}", "67890")
            
            # Handle color tags if colorize is enabled
            if handler_config.format_config.supports_colors:
                # Remove color tags for preview (or you could add actual colors)
                import re
                preview = re.sub(r'<[^>]+>', '', preview)
            
            return preview
            
        except Exception as e:
            return f"Error formatting preview: {e}"
