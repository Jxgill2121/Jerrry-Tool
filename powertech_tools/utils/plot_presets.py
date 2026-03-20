# Plot parameter preset management

import json
import os
from typing import Dict, List, Any

# Default location (inside package)
_DEFAULT_PRESETS_FILE = os.path.join(os.path.dirname(__file__), "..", "config", "plot_presets.json")

# Custom save location (user-defined)
_custom_save_path = None


def set_save_location(path: str):
    """Set a custom save location for presets"""
    global _custom_save_path
    _custom_save_path = path


def get_save_location() -> str:
    """Get the current save location"""
    return _custom_save_path or _DEFAULT_PRESETS_FILE


def load_presets() -> Dict[str, Any]:
    """Load all saved plot presets from file"""
    presets_file = get_save_location()
    if not os.path.exists(presets_file):
        return {}

    try:
        with open(presets_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading presets: {e}")
        return {}


def save_presets(presets: Dict[str, Any]):
    """Save all plot presets to file"""
    presets_file = get_save_location()
    os.makedirs(os.path.dirname(presets_file), exist_ok=True)

    try:
        with open(presets_file, "w", encoding="utf-8") as f:
            json.dump(presets, f, indent=2)
    except Exception as e:
        print(f"Error saving presets: {e}")


def save_preset(preset_name: str, graph_configs: List[Dict[str, str]]):
    """
    Save a new preset with the given name and graph configurations.

    Args:
        preset_name: Name of the preset (e.g., "R134a Standard")
        graph_configs: List of graph configuration dictionaries with keys:
            - y1_var, y2_var, y_min_var, y_max_var,
            - min_low_var, min_high_var, max_low_var, max_high_var
    """
    presets = load_presets()

    # Convert to saveable format
    preset_data = []
    for config in graph_configs:
        preset_data.append({
            "y1": config.get("y1_var", ""),
            "y2": config.get("y2_var", ""),
            "y_min": config.get("y_min_var", ""),
            "y_max": config.get("y_max_var", ""),
            "min_low": config.get("min_low_var", ""),
            "min_high": config.get("min_high_var", ""),
            "max_low": config.get("max_low_var", ""),
            "max_high": config.get("max_high_var", "")
        })

    presets[preset_name] = preset_data
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


def get_preset(preset_name: str) -> List[Dict[str, str]]:
    """Get a preset configuration by name"""
    presets = load_presets()
    return presets.get(preset_name, [])
