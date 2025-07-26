"""Logger port (interface)."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class LoggerPort(ABC):
    """Port (interface) for logging operations."""
    
    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        pass
    
    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        pass
    
    @abstractmethod
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        pass
    
    @abstractmethod
    def bind(self, **kwargs: Any) -> "LoggerPort":
        """Bind context to logger."""
        pass

