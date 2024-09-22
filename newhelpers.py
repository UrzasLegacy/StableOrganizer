# helpers.py

import os
import re
import json
import subprocess
import logging

logger = logging.getLogger(__name__)

# Constants
CATEGORIES = ["Attire", "Character", "Concept", "Style", "SFW"]
QUALITIES = ["Difficult", "Meh", "Okay", "Good", "Top", "Best"]

# Helper functions
def get_lora_directory_info(directory_name):
    """Extracts category and quality from a Lora directory name."""
    parts = directory_name.strip("_").split("_")
    if len(parts) == 2:
        category, quality = parts
        return category, quality
    return None, None

def get_png_directory_info(directory_name):
    """Extracts Lora name and category from a PNG directory name."""
    pattern = r'FindForgetYou_v2_(.*)'
    match = re.search(pattern, directory_name.replace("_TestCards", ""))
    if match:
        lora_name = match.group(1)
        parts = lora_name.split("_")
        category = parts[-1] if parts else None
        return lora_name, category
    return None, None

def get_quality_from_directory(directory_name):
    """Determines the quality from a directory name."""
    quality_map = {
        "sfw": "SFW",
        "difficult": "Difficult",
        "meh": "Meh",
        "okay": "Okay",
        "good": "Good",
        "top": "Top",
        "toptop": "Best",
        "best": "Best",
    }
    base_name = os.path.basename(directory_name.strip("_").lower())
    quality = base_name.split("_")[-1]
    return quality_map.get(quality, None)

def get_lora_name_from_file(file_name):
    """Extracts the Lora name from a .safetensors file name.
    E.g., "PONY/Attire_Good/Pony_XL_Slavic_Dress_Attire.safetensors" -> "Slavic_Dress_Attire"."""
    if file_name.endswith(".safetensors"):
        pattern = r'Pony_XL_(.*)'
        match = re.search(pattern, file_name)
        if match:
            return match.group(1)
        elif "FindForgetYou_v2_" in file_name:
            return file_name.replace("FindForgetYou_v2_", "").replace(".safetensors", "")
    return None

def open_in_explorer(path):
    """Opens a file or directory in the system file explorer."""
    if os.path.exists(path):
        if os.path.isfile(path):
            subprocess.run(['explorer', '/select,', os.path.normpath(path)])
        else:
            subprocess.run(['explorer', os.path.normpath(path)])
    else:
        logger.warning(f"Path does not exist: {path}")

def load_json_file(file_path, default=None):
    """Loads a JSON file."""
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='UTF-8') as f:
            return json.load(f)
    return default

def save_json_file(file_path, data):
    """Saves a JSON file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='UTF-8') as f:
        json.dump(data, f, indent=2)
