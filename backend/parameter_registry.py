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
        "description": "Analyzes customer frustration level throughout the call"
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
        "description": "Evaluates whether the call issue was resolved"
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


# Default Sales weights
_DEFAULT_WEIGHTS = {"talk_ratio": 10, "sentiment": 20, "empathy": 10, "resolution": 60}


def get_default_weights() -> Dict[str, float]:
    """Return the default Sales profile weights."""
    return dict(_DEFAULT_WEIGHTS)


def load_profile_config(profile_name: str = "sales") -> Dict:
    """
    Load the Sales profile configuration from client_profiles.json.

    Args:
        profile_name: Ignored — always loads 'sales'

    Returns:
        Profile dict with name, description, weights, ideal_talk_ratio
    """
    config_path = os.path.join(os.path.dirname(__file__), "config", "client_profiles.json")

    try:
        with open(config_path, "r") as f:
            profiles = json.load(f)
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        return {
            "name": "Sales",
            "description": "Optimized for closing deals — resolution matters most",
            "weights": dict(_DEFAULT_WEIGHTS),
            "ideal_talk_ratio": [0.60, 0.70]
        }

    return profiles.get("sales", {
        "name": "Sales",
        "description": "Optimized for closing deals",
        "weights": dict(_DEFAULT_WEIGHTS),
        "ideal_talk_ratio": [0.60, 0.70]
    })
