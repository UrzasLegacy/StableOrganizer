import logging
helper_logger = logging.getLogger(__name__)

import json
import os
import re
import subprocess

ROOT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

CATEGORIES = ["Attire","Character","Concept","Style","SFW"]
QUALITIES = ["Difficult", "Meh", "Okay", "Good", "Top", "Best"]

transformer = {
    "TopTop": "Best",
}

#region Helper Functions
def get_lora_directory_quality_and_category(subdirectory_path: str) -> tuple:
    """Function to get the category and type from the safetensor directory name."""
    # if subdirectory_path[:2] == "__": # Ignore folders that start with double underscore
    #     return False, False
    split = subdirectory_path.split("_")
    split = [item for item in split if item]
    if len(split) != 2:
        return False, False
    category, quality = split

    return (category, quality)


def get_png_directory_lora_name_and_category(subdirectory_path: str) -> tuple:
    """Function to get the lora name and type from the png directory name.\n
    E.g., "FindForgetYou_v2_Slavic_Dress_Attire_TestCards/FindForgetYou_v2_Slavic_Dress_Attire_TestCards_00002.png" -> (Slavic_Dress, Attire)."""
    # if subdirectory_path[:2] == "__": # Ignore folders that start with double underscore
    #     return False
    pattern = r'FindForgetYou_v2_(.*)'
    match = re.search(pattern, subdirectory_path.replace("_TestCards",""))
    if match:
        lora_name = match.group(1)
        split = lora_name.split("_")
        category = split.pop()
        return lora_name, category
    return False, False

def get_directory_quality(subdirectory_path: str) -> str:
    # if subdirectory_path[:2] == "__": # Ignore folders that start with double underscore
    #     return False
    """Function to get the quality from a lora or png directory name.\n
    E.g., "S:/Loras/Attire_Good" -> "Good" OR "S:/PNGs/good" -> "Good"."""
    t = {
        "sfw": "SFW",
        "difficult": "Difficult",
        "meh": "Meh",
        "okay": "Okay",
        "good": "Good",
        "top": "Top",
        "toptop": "Best",
        "best": "Best",
    }

    base_path = os.path.splitext(subdirectory_path.strip("_").lower())[0]
    base_name = os.path.split(base_path)[-1]
    quality = base_name.split("_")[-1] #names e.g., "Attire_Good" or "good"
    match = t.get(quality, False)

    return match

def get_lora_name(file_path: str) -> str:
    """Function to get the lora name from the safetensors file\n
    E.g., "PONY/Attire_Good/Pony_XL_Slavic_Dress_Attire.safetensors" -> "Slavic_Dress_Attire"."""
    base_path = os.path.splitext(file_path.strip("_"))[0]
    base_name = os.path.split(base_path)[-1]
    if ".safetensors" in file_path:
        pattern = r'Pony_XL_(.*)'
        match = re.search(pattern, base_name)
        if match:
            lora_name = match.group(1)
            return lora_name
    elif "FindForgetYou_v2_" in base_name:
        lora_name = base_name.replace("FindForgetYou_v2_", "")
        return lora_name
    return False

def patch_sub_lists(in_dict, specific="") -> list:
    """Recursively search in_dict for all keys that contain the specific string. If a matching key's value is a list, collect all elements from it and extend them into one out_list."""
    out_list = []

    def recurse(in_dict, specific):
        for k, v in in_dict.items():
            if specific in k.lower() and isinstance(v, list):
                out_list.extend(v)
            elif isinstance(v, dict):
                recurse(v, specific)

    recurse(in_dict, specific)
    return out_list

def patch_sub_dicts(in_dict, specific="") -> dict:
    """Recursively search in_dict for all keys that contain the specific string. If a matching key's value is a dict, collect all values from it and update them into one out_dict."""
    out_dict = {}

    def recurse(in_dict, specific):
        dict_check = isinstance(v, dict)
        for k, v in in_dict.items():
            if not dict_check:
                continue
            if specific in k.lower():
                out_dict.update(v)
            else:
                recurse(v, specific)

    recurse(in_dict, specific)
    return out_dict

def get_path_by_lora_name(dictionary, lora_name):
    """Traverse the dictionary and find the matching Lora name"""
    for _category, subcategories in dictionary.items():
        for _difficulty, loras in subcategories.items():
            for lora in loras:
                if lora[0] == lora_name:
                    return lora[1]
                
    return None

def open_to_file(file_path: str) -> None:
    """If file_path is a directory, it opens the directory. If file_path is a file, it opens the parent directory with the file selected."""
    if file_path:
        if os.path.isfile(file_path):
            subprocess.run(['explorer', '/select,', file_path])
            return True
        elif os.path.isdir(file_path):
            subprocess.run(['explorer', file_path])
            return True
    return False

def load_json_file(file: str, default=None, relative_path: bool = True):
    """Reads a json file and returns the json dict, stripping out "//" comments first."""
    if relative_path:
        file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), file)       
    else:
        file_path = file
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='UTF-8') as file:
            config = re.sub(r"(?:^|\s)//.*", "", file.read(), flags=re.MULTILINE)
        return json.loads(config)
    return default

def save_json_file(file: str, data: dict, relative_path: bool=True):
    if relative_path:
        file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), file)       
    else:
        file_path = file
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='UTF-8') as file:
        json.dump(data, file, sort_keys=False, indent=2, separators=(",", ": "))