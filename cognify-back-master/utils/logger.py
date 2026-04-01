"""
Health Drift Engine - Logging Utility
Structured logging for production monitoring
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class HealthDriftLogger:
    """Custom logger with structured output"""
    
    def __init__(
        self,
        name: str = "HealthDriftEngine",
        log_file: Optional[str] = None,
        log_level: str = "INFO"
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_format = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s'
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
    
    def info(self, message: str, **kwargs):
        """Log info message with optional context"""
        context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        full_message = f"{message} | {context}" if context else message
        self.logger.info(full_message)
    
    def warning(self, message: str, **kwargs):
        """Log warning with context"""
        context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        full_message = f"{message} | {context}" if context else message
        self.logger.warning(full_message)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error with optional exception"""
        context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        full_message = f"{message} | {context}" if context else message
        if exception:
            self.logger.error(full_message, exc_info=True)
        else:
            self.logger.error(full_message)
    
    def debug(self, message: str, **kwargs):
        """Log debug information"""
        context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        full_message = f"{message} | {context}" if context else message
        self.logger.debug(full_message)


# Global logger instance
_logger_instance: Optional[HealthDriftLogger] = None


def get_logger() -> HealthDriftLogger:
    """Get global logger instance (singleton)"""
    global _logger_instance
    if _logger_instance is None:
        from utils.config import get_config
        config = get_config()
        _logger_instance = HealthDriftLogger(
            log_file=config.log_file,
            log_level=config.log_level
        )
    return _logger_instance
