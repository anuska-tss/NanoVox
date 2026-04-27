"""
Logger Factory — Centralized logging configuration with daily rotation.

This module provides a singleton LoggerFactory that:
1. Configures logging once at startup
2. Handles daily log rotation (one file per day)
3. Allows each module to get its own logger with context

Usage:
    from utils.logger import LoggerFactory
    
    # In main.py (once at startup)
    LoggerFactory.setup()
    
    # In any other file
    logger = logging.getLogger(__name__)
    logger.info("Message from my module")
    
Result:
    logs/
    ├── backend_2026-04-22.log  (created Apr 22)
    ├── backend_2026-04-23.log  (created Apr 23)
    └── backend_2026-04-24.log  (created Apr 24, old ones auto-deleted after 7 days)
"""

import logging
import logging.handlers
import os
from datetime import datetime, timedelta


class LoggerFactory:
    """
    Centralized logging configuration.
    
    Features:
    - Daily rotating logs (one file per day)
    - Auto-cleanup of logs older than 7 days
    - Consistent format across all modules
    - Easy access via logging.getLogger(__name__)
    """
    
    _configured = False
    
    @classmethod
    def setup(cls, log_dir: str = "logs", log_level: str = "INFO", retention_days: int = 7):
        """
        Configure logging for the entire application.
        
        Args:
            log_dir (str): Directory to store logs (default: "logs")
            log_level (str): Logging level - "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
            retention_days (int): Delete logs older than this many days (default: 7)
        
        Call this ONCE at application startup (e.g., in main.py before app starts)
        """
        
        if cls._configured:
            return  # Already configured, don't do it again
        
        # Create logs directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Set root logger level
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level))
        
        # ── Daily Rotating File Handler ──
        # Creates new log file each day: backend_2026-04-22.log, backend_2026-04-23.log, etc.
        log_file_path = os.path.join(log_dir, "backend.log")
        
        # TimedRotatingFileHandler rotates at midnight (00:00)
        # "midnight" = rotate at midnight
        # interval=1 = every 1 day
        # backupCount=7 = keep last 7 days
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=log_file_path,
            when="midnight",  # Rotate at midnight
            interval=1,  # Every 1 day
            backupCount=retention_days,  # Keep last 7 days
            encoding='utf-8'
        )
        
        # Set naming pattern: backend.log.2026-04-22 (instead of default backend.log.1)
        # This makes log files date-based: backend.log.2026-04-22, backend.log.2026-04-23, etc.
        file_handler.namer = lambda name: name.replace(".log.", ".") + ".log"
        
        # ── Console Handler (optional, for development) ──
        # Logs also appear in terminal for quick debugging
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level))
        
        # ── Formatter ──
        # Format: [2026-04-22 10:15:23] module_name - INFO - Message
        formatter = logging.Formatter(
            fmt='[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Attach handlers to root logger
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Mark as configured
        cls._configured = True
        
        # Log startup message
        logger = logging.getLogger(__name__)
        logger.info(f"✅ Logging initialized: {log_dir}/backend.log (level={log_level}, retention={retention_days}d)")
    
    @staticmethod
    def get_logger(name: str):
        """
        Get a logger for a specific module.
        
        Args:
            name (str): Module name (typically __name__)
        
        Returns:
            logging.Logger: Logger instance with module context
        
        Example:
            logger = LoggerFactory.get_logger(__name__)
            logger.info("Hello from my module")
        """
        return logging.getLogger(name)


# Helper function for convenience
def get_logger(name: str):
    """
    Convenience function to get a logger.
    
    Usage:
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Message")
    """
    return logging.getLogger(name)
