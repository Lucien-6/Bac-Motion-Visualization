"""
Logging configuration module.

Provides centralized logging setup with console and file output.
"""

import logging
import os
from datetime import datetime
from pathlib import Path


def setup_root_logger(
    log_dir: str | None = None,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Set up and configure the root logger.
    
    All child loggers will inherit the root logger's handlers.
    This ensures all modules' logs are written to both console and file.

    Args:
        log_dir: Directory for log files. If None, only console output.
        level: Logging level (default: INFO).

    Returns:
        Configured root logger instance.
    """
    root_logger = logging.getLogger()
    
    if root_logger.handlers:
        return root_logger
    
    root_logger.setLevel(level)
    
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        log_filename = f"motion_vis_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(
            log_path / log_filename,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger


def setup_logger(
    name: str,
    log_dir: str | None = None,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Set up and configure a logger instance.

    Args:
        name: Logger name (typically __name__ of the calling module).
        log_dir: Directory for log files. If None, only console output.
        level: Logging level (default: INFO).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    logger.propagate = False
    
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        log_filename = f"motion_vis_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(
            log_path / log_filename,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger or create a new one with default settings.
    
    The logger will inherit handlers from the root logger if configured.

    Args:
        name: Logger name (typically __name__ of the calling module).

    Returns:
        Logger instance.
    """
    logger = logging.getLogger(name)
    return logger
