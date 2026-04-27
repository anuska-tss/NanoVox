"""
Parameter Registry

Central registry of all available analysis parameters.
The frontend reads this to dynamically generate UI cards —
no hardcoded parameter names needed in the UI.
"""
import json
import os
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

# Default registry (fallback if config doesn't define all parameters)
_DEFAULT_REGISTRY = {
    "talk_ratio": {
        "name": "talk_ratio",
        "display_name": "Talk-to-Listen Ratio",
        "icon": "🎙️",
        "description": "Measures agent vs customer speaking time balance"
    },
    "sentiment": {
        "name": "sentiment",
        "display_name": "Customer Sentiment",
        "icon": "😊",
        "description": "Analyzes customer frustration level and emotional journey throughout the call"
    },
    "empathy": {
        "name": "empathy",
        "display_name": "Agent Empathy",
        "icon": "🤝",
        "description": "Detects empathy phrases and supportive language from the agent"
    },
    "resolution": {
        "name": "resolution",
        "display_name": "Resolution Status",
        "icon": "✅",
        "description": "Detects resolution signals vs escalation/failure signals in the closing window"
    }
}


def get_available_parameters() -> List[Dict]:
    """Return list of all registered parameters with display info."""
    return [
        {
            "name": info["name"],
            "display_name": info["display_name"],
            "icon": info["icon"],
            "description": info["description"]
        }
        for info in _DEFAULT_REGISTRY.values()
    ]


# ── Profile Weight Definitions ──



# Sales profile — optimized for closing deals, with resolution weighted highest
_SALES_WEIGHTS = {"talk_ratio": 15, "sentiment": 30, "empathy": 20, "resolution": 35, "heartbeat": 0}

# Complaints profile — prioritises emotional journey and actual resolution
_COMPLAINTS_WEIGHTS = {"talk_ratio": 5, "sentiment": 35, "empathy": 20, "resolution": 40, "heartbeat": 0}

# Map profile key → weights
_PROFILE_WEIGHTS: Dict[str, Dict[str, int]] = {
    "sales": _SALES_WEIGHTS,
    "complaints": _COMPLAINTS_WEIGHTS,
}


def get_default_weights(profile: str = "complaints") -> Dict[str, float]:
    """
    Return the weight map for the given profile.

    Args:
        profile: 'sales' or 'complaints' (default: 'sales' for backward compat)

    Returns:
        Dict mapping parameter name → weight (integers summing to 100)
    """
    return dict(_PROFILE_WEIGHTS.get(profile.lower(), _SALES_WEIGHTS))


def load_profile_config(profile_name: str = "complaints") -> Dict:
    """
    Load a profile configuration from client_profiles.json.
    Falls back to built-in defaults if the file or key is missing.

    Supports profiles: 'sales', 'complaints'

    Args:
        profile_name: The profile key to load (e.g. 'sales', 'complaints')

    Returns:
        Profile dict with name, description, weights, ideal_talk_ratio
    """
    profile_key = profile_name.lower()
    config_path = os.path.join(os.path.dirname(__file__), "config", "client_profiles.json")

    try:
        with open(config_path, "r") as f:
            profiles = json.load(f)
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        profiles = {}

    # Inline fallback definitions (used when JSON doesn't have the key)
    _FALLBACKS = {
        "sales": {
            "name": "Sales",
            "description": "Optimized for closing deals — resolution matters most",
            "weights": dict(_SALES_WEIGHTS),
            "ideal_talk_ratio": [0.60, 0.70]
        },
        "complaints": {
            "name": "Complaints",
            "description": (
                "Optimized for customer complaint handling — "
                "emotional journey and actual resolution matter most"
            ),
            "weights": dict(_COMPLAINTS_WEIGHTS),
            "ideal_talk_ratio": [0.40, 0.55]
        },
    }

    if profile_key in profiles:
        return profiles[profile_key]

    logger.warning(f"Profile '{profile_key}' not found in config — using built-in fallback")
    return _FALLBACKS.get(profile_key, _FALLBACKS["sales"])
