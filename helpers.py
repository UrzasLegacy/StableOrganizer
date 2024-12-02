import os
import re
from itertools import product

ROOT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

LORA_CATEGORIES = ["Attire", "Character", "Concept", "Style"]
LORA_QUALITIES = [
    "In",
    "Scoring",
    "CloseAnalysis",
    "SFW",
    "Difficult",
    "Meh",
    "Okay",
    "Good",
    "Top",
    "Best",
]
LORA_CATEGORY_QUALITY_COMBINATIONS: list = [
    f"{category}_{quality}" for category, quality in product(LORA_CATEGORIES, LORA_QUALITIES)
]
LORA_CAT_QUAL_PATTERN = re.compile(r"\b(" + "|".join(LORA_CATEGORY_QUALITY_COMBINATIONS) + r")\b")

CKPT_CATEGORIES = ["Drawn", "Semi", "Real"]
CKPT_QUALITIES = [
    "In",
    "Scoring",
    "CloseAnalysis",
    "SFW",
    "Meh",
    "Okay",
    "Good",
    "Top",
]
CKPT_CATEGORY_QUALITY_COMBINATIONS: list = [
    f"{category}_{quality}" for category, quality in product(CKPT_CATEGORIES, CKPT_QUALITIES)
]
CKPT_CAT_QUAL_PATTERN = re.compile(r"\b(" + "|".join(CKPT_CATEGORY_QUALITY_COMBINATIONS) + r")\b")