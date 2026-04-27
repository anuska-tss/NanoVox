"""
Config Loader — Load backend configuration from JSON file.

This module provides a centralized way to load configuration values
from backend_config.json. If the file is missing or invalid, sensible
defaults are used.

Usage:
    from utils.config_loader import load_config
    config = load_config()
    
    # Access nested values
    port = config['server']['port']
    max_size = config['upload']['max_file_size_mb']
"""

import json
import os
import logging

logger = logging.getLogger(__name__)


def load_config():
    """
    Load backend configuration from backend_config.json.
    
    Returns:
        dict: Configuration object with all settings.
              If file is missing or invalid, returns built-in defaults.
    
    Config structure:
        {
            "server": { "host", "port" },
            "upload": { "max_file_size_mb" },
            "logging": { "level", "file_name", "format" },
            "ml_models": { "whisper_model" },
            "threading": { "max_workers" },
            "speaker_detection": { "pause_gap_seconds", "anchor_bonus_points", "closer_bonus_points" },
            "profiles": { "default" },
            "cors": { "allowed_origins" }
        }
    """
    
    # Default configuration (fallback if file is missing)
    default_config = {
        "server": {
            "host": "0.0.0.0",
            "port": 8000
        },
        "upload": {
            "max_file_size_mb": 50
        },
        "logging": {
            "level": "INFO",
            "file_name": "backend_debug.log",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "ml_models": {
            "whisper_model": "tiny"
        },
        "threading": {
            "max_workers": 4
        },
        "speaker_detection": {
            "pause_gap_seconds": 0.3,
            "anchor_bonus_points": 12,
            "closer_bonus_points": 6
        },
        "profiles": {
            "default": "sales"
        },
        "cors": {
            "allowed_origins": [
                "http://localhost:5173",
                "http://localhost:5174"
            ]
        }
    }
    
    # Try to load from config file
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "backend_config.json")
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                logger.info(f"✅ Loaded backend config from {config_path}")
                return file_config
        else:
            logger.warning(f"⚠️  Config file not found at {config_path}. Using defaults.")
            return default_config
    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to parse config JSON: {e}. Using defaults.")
        return default_config
    except Exception as e:
        logger.error(f"❌ Error loading config: {e}. Using defaults.")
        return default_config


def get_max_upload_size_bytes():
    """
    Get max upload size in bytes.
    
    Returns:
        int: Maximum file size in bytes (from config, converted from MB)
    """
    config = load_config()
    size_mb = config['upload']['max_file_size_mb']
    return size_mb * 1024 * 1024
