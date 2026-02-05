"""
Logging utility for AI Employee system.

Provides consistent logging across all components with both console and file output.
Logs are written to the vault's Logs/ folder for easy access from Obsidian.
"""

import logging
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def get_logger(name: str, log_level: str = None) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__ of the calling module)
        log_level: Optional log level override (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    # Get or create logger
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        # Determine log level
        if log_level is None:
            log_level = os.getenv('LOG_LEVEL', 'INFO')

        level = getattr(logging, log_level.upper(), logging.INFO)
        logger.setLevel(level)

        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )

        # Console handler (stdout)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File handler (vault logs)
        try:
            vault_path = Path(os.getenv('VAULT_PATH', '/mnt/d/AI_EMPLOYEE_VAULT'))
            logs_dir = vault_path / 'Logs'
            logs_dir.mkdir(parents=True, exist_ok=True)

            # Create log file with date in name
            log_filename = f"ai_employee_{datetime.now().strftime('%Y%m%d')}.log"
            log_file = logs_dir / log_filename

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(detailed_formatter)
            logger.addHandler(file_handler)

        except Exception as e:
            # If file logging fails, log to console only
            logger.warning(f"Could not set up file logging: {e}")

        # Prevent propagation to root logger
        logger.propagate = False

    return logger


def configure_dev_logging():
    """
    Configure verbose logging for development mode.
    Sets all loggers to DEBUG level.
    """
    logging.getLogger().setLevel(logging.DEBUG)
    for handler in logging.getLogger().handlers:
        handler.setLevel(logging.DEBUG)


if __name__ == '__main__':
    # Test the logger
    test_logger = get_logger('test')
    test_logger.debug('This is a debug message')
    test_logger.info('This is an info message')
    test_logger.warning('This is a warning message')
    test_logger.error('This is an error message')
    test_logger.critical('This is a critical message')

    print("\n✓ Logger test complete. Check logs in vault Logs/ folder.")
