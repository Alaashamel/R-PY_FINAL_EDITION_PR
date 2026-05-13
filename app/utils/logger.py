import os
import sys

from loguru import logger

os.makedirs("logs", exist_ok=True)

logger.remove()

# Developer-friendly console logs.
logger.add(
    sys.stdout,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{extra[context]}</cyan> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
    level="INFO",
)

# Human-readable daily API log.
logger.add(
    "logs/api_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[context]} | {name}:{function}:{line} - {message}",
    level="DEBUG",
)

# Machine-readable structured log file for dashboards/log processors.
logger.add(
    "logs/structured_{time:YYYY-MM-DD}.json",
    rotation="1 day",
    retention="30 days",
    compression="zip",
    serialize=True,
    level="DEBUG",
)

# Separate error log used by /monitoring/recent-errors.
logger.add(
    "logs/error_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[context]} | {name}:{function}:{line} - {message}",
)

logger = logger.bind(context="app")
request_logger = logger.bind(context="request")
auth_logger = logger.bind(context="auth")
error_logger = logger.bind(context="error")
