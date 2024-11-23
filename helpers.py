import os
from itertools import product
import re

ROOT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
CATEGORIES = ["Attire","Character","Concept","Style"]
QUALITIES = ["In", "Scoring", "CloseAnalysis", "SFW", "Difficult", "Meh", "Okay", "Good", "Top", "Best"]
CATEGORY_QUALITY_COMBINATIONS: list = [f"{category}_{quality}" for category, quality in product(CATEGORIES, QUALITIES)]
CAT_QUAL_PATTERN = re.compile("|".join(CATEGORY_QUALITY_COMBINATIONS))


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

