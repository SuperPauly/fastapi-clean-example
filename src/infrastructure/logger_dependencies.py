"""Dependency injection for logger configuration tool."""

from functools import lru_cache

# Logger configuration imports
from src.infrastructure.config.logger_config_adapter import DynaconfLoggerConfigAdapter
from src.infrastructure.logging.loguru_config_adapter import LoguruConfigAdapter
from src.application.ports.logger_configuration import LoggerConfigurationPort, LoggerApplicationPort


@lru_cache()
def get_logger_config_port() -> LoggerConfigurationPort:
    """Get logger configuration port instance.
    
    This function provides the configuration persistence adapter for
    the Loguru configuration tool, using Dynaconf for storage.
    
    Returns:
        LoggerConfigurationPort: Configuration persistence adapter
    """
    return DynaconfLoggerConfigAdapter()


@lru_cache()
def get_logger_application_port() -> LoggerApplicationPort:
    """Get logger application port instance.
    
    This function provides the Loguru integration adapter for
    applying configurations to the actual logger.
    
    Returns:
        LoggerApplicationPort: Loguru integration adapter
    """
    return LoguruConfigAdapter()


async def get_logger_config_dependencies() -> tuple[LoggerConfigurationPort, LoggerApplicationPort]:
    """Get logger configuration dependencies.
    
    This function provides both ports needed for the logger configuration
    tool, following the hexagonal architecture pattern.
    
    Returns:
        tuple: (config_port, logger_port) for dependency injection
    """
    config_port = get_logger_config_port()
    logger_port = get_logger_application_port()
    
    return config_port, logger_port
