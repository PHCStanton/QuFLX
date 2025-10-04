"""
Simple logging configuration for QuantumFlux Trading Platform.

Compatible with the capabilities framework.
"""

import logging
import sys
from typing import Optional


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def log_performance(func_name: str, duration: float, memory_usage: float = 0.0, **kwargs):
    """Log performance metrics."""
    logger = get_logger("quantumflux.performance")
    logger.info(f"Performance: {func_name} - Duration: {duration:.3f}s, Memory: {memory_usage:.2f}MB")


def log_security_event(event_type: str, user: str = None, ip: str = None, details: dict = None):
    """Log security-related events."""
    logger = get_logger("quantumflux.security")
    message = f"Security event: {event_type}"
    if details:
        message += f" - {details}"
    logger.warning(message)


def log_api_request(method: str, path: str, status_code: int, duration: float, user_agent: str = None):
    """Log API request details."""
    logger = get_logger("quantumflux.api")
    logger.info(f"API Request: {method} {path} -> {status_code} ({duration:.3f}s)")


# Global logger instances
app_logger = get_logger("quantumflux.app")
api_logger = get_logger("quantumflux.api")
performance_logger = get_logger("quantumflux.performance")
security_logger = get_logger("quantumflux.security")
error_logger = get_logger("quantumflux.error")