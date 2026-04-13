# Fuel systems validation preset management

import json
import os
from typing import Dict, List, Any

# Default location (inside package)
_DEFAULT_PRESETS_FILE = os.path.join(os.path.dirname(__file__), "..", "config", "fuel_systems_presets.json")

# Custom save location (user-defined)
_custom_save_path = None


def set_save_location(path: str):
    """Set a custom save location for fuel systems presets"""
    global _custom_save_path
    _custom_save_path = path


def get_save_location() -> str:
    """Get the current save location"""
    return _custom_save_path or _DEFAULT_PRESETS_FILE


def load_presets() -> Dict[str, Any]:
    """Load all saved fuel systems validation presets from file"""
    presets_file = get_save_location()
    if not os.path.exists(presets_file):
        return {}

    try:
        with open(presets_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading fuel systems presets: {e}")
        return {}


def save_presets(presets: Dict[str, Any]):
    """Save all fuel systems validation presets to file"""
    presets_file = get_save_location()
    os.makedirs(os.path.dirname(presets_file), exist_ok=True)

    try:
        with open(presets_file, "w", encoding="utf-8") as f:
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
