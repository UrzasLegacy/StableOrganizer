import os
import re
from itertools import product

ROOT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
CATEGORIES = ["Attire","Character","Concept","Style"]
QUALITIES = ["In", "Scoring", "CloseAnalysis", "SFW", "Difficult", "Meh", "Okay", "Good", "Top", "Best"]
CATEGORY_QUALITY_COMBINATIONS: list = [f"{category}_{quality}" for category, quality in product(CATEGORIES, QUALITIES)]
CAT_QUAL_PATTERN = re.compile(r'\b(' + '|'.join(CATEGORY_QUALITY_COMBINATIONS) + r')\b')