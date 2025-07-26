"""Loguru logger adapter."""

from typing import Any
from loguru import logger

from src.application.ports.logger import LoggerPort


class LoguruLoggerAdapter(LoggerPort):
    """Loguru implementation of the logger port."""
    
    def __init__(self, logger_instance=None):
        """Initialize the logger adapter."""
        self._logger = logger_instance or logger
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self._logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        self._logger.critical(message, **kwargs)
    
    def bind(self, **kwargs: Any) -> "LoguruLoggerAdapter":
        """Bind context to logger."""
        bound_logger = self._logger.bind(**kwargs)
        return LoguruLoggerAdapter(bound_logger)

