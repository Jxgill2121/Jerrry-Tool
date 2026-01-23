# Fuel systems validation preset management

import json
import os
from typing import Dict, List, Any


PRESETS_FILE = os.path.join(os.path.dirname(__file__), "..", "config", "fuel_systems_presets.json")


def load_presets() -> Dict[str, Any]:
    """Load all saved fuel systems validation presets from file"""
    if not os.path.exists(PRESETS_FILE):
        return {}

    try:
        with open(PRESETS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading fuel systems presets: {e}")
        return {}


def save_presets(presets: Dict[str, Any]):
    """Save all fuel systems validation presets to file"""
    os.makedirs(os.path.dirname(PRESETS_FILE), exist_ok=True)

    try:
        with open(PRESETS_FILE, "w", encoding="utf-8") as f:
            json.dump(presets, f, indent=2)
    except Exception as e:
        print(f"Error saving fuel systems presets: {e}")


def save_preset(preset_name: str, config: Dict[str, Any]):
    """
    Save a new fuel systems validation preset.

    Args:
        preset_name: Name of the preset (e.g., "R134a Standard")
        config: Configuration dictionary with:
            - ptank_threshold: float
            - tfuel_target: float
            - tfuel_window: float
            - param_limits: Dict[str, Dict[str, float]]
    """
    presets = load_presets()
    presets[preset_name] = config
    save_presets(presets)


def delete_preset(preset_name: str):
    """Delete a preset by name"""
    presets = load_presets()
    if preset_name in presets:
        del presets[preset_name]
        save_presets(presets)


def get_preset_names() -> List[str]:
    """Get list of all preset names"""
    presets = load_presets()
    return sorted(presets.keys())


def get_preset(preset_name: str) -> Dict[str, Any]:
    """Get a preset configuration by name"""
    presets = load_presets()
    return presets.get(preset_name, {})
