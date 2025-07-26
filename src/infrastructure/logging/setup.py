"""Logging setup and configuration."""

import sys
from pathlib import Path
from loguru import logger

from src.infrastructure.config.settings import logging_config


def setup_logging() -> None:
    """Configure Loguru logging."""
    # Remove default handler
    logger.remove()
    
    # Create logs directory if it doesn't exist
    log_file_path = Path(logging_config.file_path)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Add console handler
    logger.add(
        sys.stdout,
        level=logging_config.level,
        format=logging_config.format,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # Add file handler
    logger.add(
        log_file_path,
        level=logging_config.level,
        format=logging_config.format,
        rotation="10 MB",
        retention="30 days",
        compression="gz",
        backtrace=True,
        diagnose=True,
    )
    
    # Add error file handler
    error_log_path = log_file_path.parent / "error.log"
    logger.add(
        error_log_path,
        level="ERROR",
        format=logging_config.format,
        rotation="10 MB",
        retention="30 days",
        compression="gz",
        backtrace=True,
        diagnose=True,
    )
    
    logger.info("Logging configured successfully")

