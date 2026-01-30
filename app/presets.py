"""Video compression presets configuration.

Defines preset profiles for different compression levels:
- light: up to 1080p, minimal compression (fast)
- medium: up to 720p, moderate compression (balanced)
- strong: up to 480p, aggressive compression (slow)
"""

from typing import TypedDict


class PresetConfig(TypedDict):
    """Configuration for a compression preset."""
    max_height: int
    video_kbps_mult: float
    crf: int
    preset: str


PRESETS: dict[str, PresetConfig] = {
    "light": {
        "max_height": 1080,
        "video_kbps_mult": 1.0,
        "crf": 20,
        "preset": "slow"
    },
    "medium": {
        "max_height": 720,
        "video_kbps_mult": 0.75,
        "crf": 23,
        "preset": "slow"
    },
    "strong": {
        "max_height": 480,
        "video_kbps_mult": 0.5,
        "crf": 28,
        "preset": "medium"
    }
}


def get_preset(preset_name: str) -> PresetConfig:
    """Retrieve preset configuration by name.
    
    Args:
        preset_name: Preset name ('light', 'medium', or 'strong')
        
    Returns:
        PresetConfig dictionary with compression parameters
        
    Raises:
        KeyError: If preset name is not found
    """
    if preset_name not in PRESETS:
        raise KeyError(f"Unknown preset: {preset_name}. Available: {list(PRESETS.keys())}")
    return PRESETS[preset_name]


def list_presets() -> list[str]:
    """Get list of available preset names.
    
    Returns:
        List of preset names
    """
    return list(PRESETS.keys())
