import logging
import os
import re

from itertools import product

from helpers import CATEGORIES, QUALITIES


ROOT_DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logger = logging.getLogger(__name__)

def recursive_fetch(dictionary, key):
    for k, v in dictionary.items():
        if k == key:
            return v
        if isinstance(v, dict):
            result = recursive_fetch(v, key)
            if result is not None:
                return result
    return None
class InfoHandler():
    """

    """

#region Init
    def __init__(self, config_data: dict = None) -> None:
        self.lora_model_dir: str = None
        self.lora_png_dir: str = None
        self.ckpt_model_dir: str = None
        self.ckpt_png_dir: str = None
        self.output_dir: str = None
        self.everything_dir: str = None

        self.category_quality_combinations: list = [f"{category}_{quality}" for category, quality in product(CATEGORIES, QUALITIES)]

        self.cat_qual_pattern = self.init_regex_pattern(self.category_quality_combinations)
        self._init_dirs(config_data)



    def get_dirs(self) -> tuple[str, str, str]:
        return self.lora_model_dir, self.lora_png_dir, self.output_dir


    def _init_dirs(self, config_data: dict):
        self.lora_model_dir: str = config_data.get('lora_model_dir')
        self.lora_png_dir: str = config_data.get('lora_png_dir')
        self.ckpt_model_dir: str = config_data.get('ckpt_model_dir')
        self.ckpt_png_dir: str = config_data.get('ckpt_png_dir')
        self.output_dir: str = config_data.get('output_dir')
        self.everything_dir: str = config_data.get('everything_dir')


#region Public Utils

    def get_unified_lora_dictionaryOLD(self) -> dict[str, dict[str, dict[str, tuple[str | None, str | None]]]]:
        """Initialize a dictionary with the required structure, lora model dependent!"""
        unified_dict = self.initialize_dictionary_template()
        lora_dict = self.build_lora_dictionary()
        png_dict = self.build_png_dictionary()
        for category, qualities in lora_dict.items():
            for quality, loras in qualities.items():
                for lora_name, model_path in loras.items():
                    png_path = recursive_fetch(png_dict, lora_name)
                    unified_dict[category][quality][lora_name] = (model_path, png_path)
        return unified_dict


    def get_unified_lora_dictionary(self) -> dict[str, dict[str, dict[str, tuple[str | None, str | None]]]]:
        """Create a unified dictionary with all available information, prioritizing lora subcategories."""
        unified_dict = self.initialize_dictionary_template()
        lora_dict = self.build_lora_dictionary()
        png_dict = self.build_png_dictionary()

        # Track processed loras to avoid duplicates across categories
        seen_loras = {}

        # Combine all categories
        #all_categories = set(lora_dict.keys()).union(png_dict.keys())
        all_categories = sorted(set(lora_dict.keys()).union(png_dict.keys()), key=InfoHandler._category_sort_key)
        for category in all_categories:
            unified_dict.setdefault(category, {})
            lora_qualities = lora_dict.get(category, {})
            png_qualities = png_dict.get(category, {})

            # Combine all qualities
            all_qualities = set(lora_qualities.keys()).union(png_qualities.keys())
            for quality in sorted(all_qualities, key=InfoHandler._quality_sort_key):
                unified_dict[category].setdefault(quality, {})
                loras = lora_qualities.get(quality, {})
                pngs = png_qualities.get(quality, {})

                # Combine all lora names
                all_lora_names = set(loras.keys()).union(pngs.keys())
                for lora_name in sorted(all_lora_names):
                    model_path = loras.get(lora_name)
                    png_path = pngs.get(lora_name)

                    # Handle duplicates
                    if lora_name in seen_loras:
                        # Merge into the already processed category/quality
                        existing_category, existing_quality = seen_loras[lora_name]
                        unified_entry = unified_dict[existing_category][existing_quality][lora_name]
                        unified_entry = (
                            unified_entry[0] or model_path,  # Keep the existing model_path or use the new one
                            unified_entry[1] or png_path,    # Keep the existing png_path or use the new one
                        )
                        unified_dict[existing_category][existing_quality][lora_name] = unified_entry
                    else:
                        # First time seeing this lora_name
                        unified_dict[category][quality][lora_name] = (model_path, png_path)

                        # If this lora_name has a lora file, prioritize this category/quality
                        if model_path:
                            seen_loras[lora_name] = (category, quality)

        # Clean up empty qualities
        for category in list(unified_dict.keys()):
            for quality in list(unified_dict[category].keys()):
                if not unified_dict[category][quality]:
                    del unified_dict[category][quality]

        return unified_dict


    def reunify_lora_dictionary(self, dirty_dict) -> dict[str, dict[str, dict[str, tuple[str | None, str | None]]]]:
        """Create a unified dictionary with all available information in dirty dictionary, prioritizing lora subcategories."""
        unified_dict = self.initialize_dictionary_template()

        # Track processed loras to avoid duplicates across categories
        seen_loras = {}

        # Combine all categories
        all_categories = dirty_dict.keys()
        for category in all_categories:
            unified_dict.setdefault(category, {})
            lora_qualities = dirty_dict.get(category, {})

            # Combine all qualities
            all_qualities = lora_qualities.keys()
            for quality in all_qualities:
                unified_dict[category].setdefault(quality, {})
                loras = dirty_dict[category].get(quality, {})

                # Combine all lora names
                all_lora_names = loras.keys()
                for lora_name in all_lora_names:
                    model_path, png_path = dirty_dict[category][quality].get(lora_name)

                    # Handle duplicates
                    if lora_name in seen_loras:
                        # Merge into the already processed category/quality
                        existing_category, existing_quality = seen_loras[lora_name]
                        unified_entry = unified_dict[existing_category][existing_quality][lora_name]
                        unified_entry = [
                            unified_entry[0] or model_path,  # Keep the existing model_path or use the new one
                            unified_entry[1] or png_path,    # Keep the existing png_path or use the new one
                        ]
                        unified_dict[existing_category][existing_quality][lora_name] = unified_entry
                    else:
                        # First time seeing this lora_name
                        unified_dict[category][quality][lora_name] = [model_path, png_path]

                        # If this lora_name has a lora file, prioritize this category/quality
                        if model_path:
                            seen_loras[lora_name] = (category, quality)

        # Clean up empty qualities
        for category in list(unified_dict.keys()):
            for quality in list(unified_dict[category].keys()):
                if not unified_dict[category][quality]:
                    del unified_dict[category][quality]

        return unified_dict


    def build_png_dictionary(self) -> dict[str, dict[str, dict[str, str]]]:
        """Create an organized dictionary of png directories with structure category:quality:[(lora_name, lora_path)]."""
        png_directory_dict = {}
        for folder in os.listdir(self.lora_png_dir):
            quality = self._get_directory_quality(folder)
            if not quality:
                continue
            category = self._get_directory_category(folder)
            if not category:
                continue
            png_directory_dict.setdefault(category, {}).setdefault(quality, {})
            folder_path = os.path.join(self.lora_png_dir, folder)
            for lora_png_directory in os.listdir(folder_path):
                lora_name, lora_category = self._get_lora_name_and_category_from_png_directory(lora_png_directory)
                if not lora_name:
                    continue
                absolute_path = os.path.normpath(os.path.join(folder_path, lora_png_directory))
                png_directory_dict[category][quality][lora_name] = absolute_path
        return self.sort_built_dictionary(png_directory_dict)


    def build_lora_dictionary(self) -> dict[str, dict[str, dict[str, str]]]:
        """Create an organized dictionary of loras with structure category:quality:[(lora_name, lora_path), ...]"""
        lora_model_dict = {}
        for folder in os.listdir(self.lora_model_dir):
            quality = self._get_directory_quality(folder)
            if not quality:
                continue
            category = self._get_directory_category(folder)
            if not category:
                continue
            lora_model_dict.setdefault(category, {}).setdefault(quality, {})
            folder_path = os.path.join(self.lora_model_dir, folder)
            for file in os.listdir(folder_path):
                if file.endswith(".safetensors"):
                    lora_name = self._get_lora_name_from_model_filepath(file)
                    if not lora_name:
                        continue
                    absolute_path = os.path.normpath(os.path.join(folder_path, file))
                    lora_model_dict[category][quality][lora_name] = absolute_path
        return self.sort_built_dictionary(lora_model_dict)


    @staticmethod
    def initialize_dictionary_template():
        return {category: {quality: {} for quality in QUALITIES} for category in CATEGORIES}


    def find_hanging_png_directoriesOLD(self):
        lora_dict = self.build_lora_dictionary()
        png_dict = self.build_png_dictionary()
        hanging = []
        for category, qualities in png_dict.items():
            for quality, loras in qualities.items():
                for lora_name, png_path in loras.items():
                    if not recursive_fetch(lora_dict, lora_name):
                        hanging.append((lora_name, png_path))
        if len(hanging):
            for png_path in hanging:
                print(f"Hanging PNG directory: {*png_path,}")
            return True
        return False


    def find_hanging_png_directories(self):
        lora_dict = self.get_unified_lora_dictionary()
        hanging = []
        for category, qualities in lora_dict.items():
            for quality, loras in qualities.items():
                for lora_name, (model_path, png_path) in loras.items():
                    if png_path and not model_path:
                        hanging.append((lora_name, png_path))
        if len(hanging):
            for png_path in hanging:
                print(f"Hanging PNG directory: {*png_path,}")
            return True
        return False



    def get_quality_from_filepath(self, filepath: str) -> str:
        """Function to get the quality from directory or safetensors/png files.\n
        E.g., "PONY/Attire_Good/Pony_XL_Slavic_Dress_Attire.safetensors" -> "Good"
        "X:\CardArchive\LoraCards\Attire_Scoring\FindForgetYou_v2_Slavic_Dress_Attire_TestCards" -> "Good"
        "X:\CardArchive\LoraCards\Attire_Scoring\FindForgetYou_v2_Slavic_Dress_Attire_TestCards\FindForgetYou_v2_Slavic_Dress_Attire_TestCards_00001.png" -> "Good".
        """

        match = self.cat_qual_pattern.search(filepath)
        return match.group() if match else "None"


    @staticmethod
    def get_paths_by_lora_name(dictionary, lora_name) -> str:
        """Traverse the dictionary and find the matching Lora name."""
        for _category, qualities in dictionary.items():
            for _quality, loras in qualities.items():
                for lora_key, (lora_model_path, lora_png_path) in loras.items():
                    if lora_key == lora_name:
                        return lora_model_path, lora_png_path
        return "None"

    @staticmethod
    def init_regex_pattern(category_quality_combinations):
        return re.compile("|".join(category_quality_combinations))


    @staticmethod
    def sort_built_dictionary(built_dictionary: dict) -> dict:
        """Sort the dictionary by category and quality keys."""
        sorted_lora_directory_dict = {
            category: {
                quality: dict(sorted(loras.items()))
                for quality, loras in sorted(qualities.items(), key=lambda q: InfoHandler._quality_sort_key(q[0]), reverse=True)
            }
            for category, qualities in sorted(built_dictionary.items(), key=lambda q: InfoHandler._category_sort_key(q[0]), reverse=True)
        }
        return sorted_lora_directory_dict

    @staticmethod
    def _category_sort_key(category):
        """Use the index in CATEGORIES for sorting; if category is not found, assign a high index."""
        return CATEGORIES.index(category) if category in CATEGORIES else len(CATEGORIES)

    @staticmethod
    def _quality_sort_key(quality):
        """Use the index in QUALITIES for sorting; if quality is not found, assign a high index."""
        return QUALITIES.index(quality) if quality in QUALITIES else len(QUALITIES)


    @staticmethod
    def _get_directory_category(subdirectory_name: str) -> str:
        """Function to get the category from a lora or png directory name.\n
        E.g., "S:/Loras/Attire_Good" -> "Good" OR "S:/PNGs/good" -> "Good"."""
        category_map = {
            "attire": "Attire",
            "character": "Character",
            "concept": "Concept",
            "style": "Style",
        }
        base_name = os.path.basename(subdirectory_name.strip("_"))
        category = base_name.split("_")[0].lower()
        return category_map.get(category, None)


    @staticmethod
    def _get_directory_quality(subdirectory_name: str) -> str:
        """Function to get the quality from a lora or png directory name.\n
        E.g., "S:/Loras/Attire_Good" -> "Good" OR "S:/PNGs/good" -> "Good"."""
        quality_map = {
            "sfw": "SFW",
            "scoring": "Scoring",
            "closeanalysis": "CloseAnalysis",
            "difficult": "Difficult",
            "meh": "Meh",
            "okay": "Okay",
            "good": "Good",
            "top": "Top",
            "toptop": "Best",
            "best": "Best",
            "in": "In",
        }
        base_name = os.path.basename(subdirectory_name.strip("_"))
        quality = base_name.split("_")[-1].lower()
        return quality_map.get(quality, None)


    @staticmethod
    def _get_lora_name_from_model_filepath(filepath: str) -> str:
        """Function to get the lora name from directory or safetensors/png files.\n
        E.g., "PONY/Attire_Good/Pony_XL_Slavic_Dress_Attire.safetensors" -> "Slavic_Dress_Attire"
        "X:\CardArchive\LoraCards\Attire_Scoring\FindForgetYou_v2_Slavic_Dress_Attire_TestCards" -> "Slavic_Dress_Attire".
        "X:\CardArchive\LoraCards\Attire_Scoring\FindForgetYou_v2_Slavic_Dress_Attire_TestCards\FindForgetYou_v2_Slavic_Dress_Attire_TestCards_00001.png -> (Slavic_Dress, Attire)".
        """
        base_path = os.path.splitext(filepath.strip("_"))[0]
        base_name = os.path.split(base_path)[-1]
        if ".safetensors" in filepath:
            pattern = r'Pony_XL_(.*)'
            match = re.search(pattern, base_name)
            if match:
                lora_name = match.group(1)
                return lora_name
            else:
                logger.debug(f"{base_name} is not formatted properly. Missing 'Pony_XL_'")
        elif "FindForgetYou_v2_" in base_name:
            if ".png" in filepath:
                base_path = os.path.dirname(filepath.strip("_"))
                base_name = os.path.split(base_path)[-1]
            lora_name = base_name.replace("FindForgetYou_v2_", "").replace("_TestCards", "")
            return lora_name
        return False


    @staticmethod
    def _get_lora_name_and_category_from_png_directory(subdirectory_name: str) -> tuple:
        """Get the lora name and category from the png directory name.\n
        E.g., "FindForgetYou_v2_Slavic_Dress_Attire_TestCards/FindForgetYou_v2_Slavic_Dress_Attire_TestCards" -> (Slavic_Dress, Attire)."""
        # if subdirectory_name[:2] == "__": # Ignore folders that start with double underscore
        #     return False
        pattern = r'FindForgetYou_v2_(.*)'
        match = re.search(pattern, subdirectory_name.replace("_TestCards",""))
        if match:
            lora_name = match.group(1)
            split = lora_name.split("_")
            category = split.pop()
            return lora_name, category
        return False, False





