"""
Centralized logging configuration using loguru.

This module initializes and configures logging for the entire application.
Configuration is driven by logging_config.yaml with environment variable overrides.

Usage:
    from core.logger import get_logger
    
    logger = get_logger(__name__)
    logger.info("Processing started", extra={"image": "test.png"})
"""

import os
import sys
from pathlib import Path
from loguru import logger
import yaml
from typing import Optional, Dict, Any


# Default configuration (used if logging_config.yaml is not found)
DEFAULT_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "environment": os.getenv("ENVIRONMENT", "dev"),
    "log_directory": os.getenv("LOG_DIRECTORY", "logs"),
    "log_level": os.getenv("LOG_LEVEL", "INFO"),
    "log_format": os.getenv("LOG_FORMAT", "plain"),  # plain or json
    "rotation": {
        "type": "daily",
        "retention": "all"
    }
}

_logger_initialized = False
_config_cache = None


def load_config() -> Dict[str, Any]:
    """
    Load logging configuration from YAML file with environment variable overrides.
    
    Priority:
    1. Environment variables (LOG_LEVEL, LOG_FORMAT, LOG_DIRECTORY, ENVIRONMENT)
    2. logging_config.yaml file
    3. DEFAULT_CONFIG
    
    Returns:
        Dictionary containing logger configuration
    """
    global _config_cache
    
    if _config_cache is not None:
        return _config_cache
    
    config = DEFAULT_CONFIG.copy()
    
    # Try to load from YAML config file
    config_file = Path(__file__).parent.parent / "logging_config.yaml"
    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                yaml_config = yaml.safe_load(f) or {}
                config.update(yaml_config)
        except Exception as e:
            print(f"Warning: Failed to load {config_file}: {e}. Using defaults.", file=sys.stderr)
    
    # Environment variable overrides (these take priority)
    if os.getenv("LOG_LEVEL"):
        config["log_level"] = os.getenv("LOG_LEVEL")
    if os.getenv("LOG_FORMAT"):
        config["log_format"] = os.getenv("LOG_FORMAT")
    if os.getenv("LOG_DIRECTORY"):
        config["log_directory"] = os.getenv("LOG_DIRECTORY")
    if os.getenv("ENVIRONMENT"):
        config["environment"] = os.getenv("ENVIRONMENT")
    
    _config_cache = config
    return config


def initialize_logger() -> None:
    """
    Initialize loguru with configuration from config file and environment variables.
    
    Sets up:
    - File handler with rotation
    - Console handler (optional, based on environment)
    - Log level and format
    
    This should be called once at application startup.
    """
    global _logger_initialized
    
    if _logger_initialized:
        return
    
    config = load_config()
    
    # Remove default stderr handler
    logger.remove()
    
    # Create logs directory if it doesn't exist
    log_dir = Path(config["log_directory"])
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine log format
    if config["log_format"] == "json":
        log_format = "{message}"  # Let loguru serialize to JSON
        is_json = True
    else:
        # Plain text format with timestamp, level, module, function, message
        log_format = (
            "<level>{time:YYYY-MM-DD HH:mm:ss}</level> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
        is_json = False
    
    # File handler - always enabled
    log_file = log_dir / "app.log"
    
    # Handle rotation based on configuration
    rotation_config = config.get("rotation", {})
    rotation = None
    retention = None
    
    if rotation_config.get("type") == "daily":
        rotation = "00:00"  # Rotate at midnight
    elif rotation_config.get("type") == "size":
        rotation = rotation_config.get("size", "100 MB")
    
    if rotation_config.get("retention") == "all":
        retention = None  # Keep all files
    elif rotation_config.get("retention"):
        retention = rotation_config.get("retention")
    
    # Add file handler
    if is_json:
        logger.add(
            sink=str(log_file),
            format=log_format,
            level=config["log_level"],
            rotation=rotation,
            retention=retention,
            serialize=True,  # Output as JSON
            colorize=False,
        )
    else:
        logger.add(
            sink=str(log_file),
            format=log_format,
            level=config["log_level"],
            rotation=rotation,
            retention=retention,
            colorize=False,
        )
    
    # Console handler - only in dev/debug
    environment = config.get("environment", "dev")
    if environment in ("dev", "debug"):
        if is_json:
            # For JSON in console, use plain format for readability
            console_format = (
                "<level>{time:YYYY-MM-DD HH:mm:ss}</level> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                "<level>{message}</level>"
            )
        else:
            console_format = log_format
        
        logger.add(
            sink=sys.stderr,
            format=console_format,
            level=config["log_level"],
            colorize=True,
        )
    
    _logger_initialized = True
    
    # Log initialization
    logger.info(
        f"Logger initialized | Environment: {environment} | "
        f"Level: {config['log_level']} | Format: {config['log_format']} | "
        f"LogDir: {log_dir}"
    )


def get_logger(name: str):
    """
    Get a logger instance for a module.
    
    Args:
        name: Module name (typically __name__)
    
    Returns:
        Configured loguru logger instance
    
    Example:
        logger = get_logger(__name__)
        logger.info("Starting process", extra={"status": "ok"})
    """
    # Ensure logger is initialized on first call
    if not _logger_initialized:
        initialize_logger()
    
    # Bind module name to logger
    return logger.bind(module=name)


def set_log_level(level: str) -> None:
    """
    Dynamically change log level at runtime.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logger.remove()
    config = load_config()
    config["log_level"] = level
    _config_cache = config
    initialize_logger()
