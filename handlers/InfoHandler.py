import logging
import os
import re

from itertools import product

from helpers import CATEGORIES, QUALITIES


ROOT_DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logger = logging.getLogger(__name__)




class InfoHandler():


    """
    Container for various functions that return info for the FileHandler class.





    """


    def __init__(self, config_data: dict = None) -> None:
        self.lora_model_dir = config_data.get('lora_model_dir')
        self.lora_png_dir = config_data.get('lora_png_dir')
        self.output_dir = config_data.get('output_dir')

        self.cq_pattern = None
        self._init_regex_patterns()


    def _init_regex_patterns(self):
        CATEGORY_QUALITY_COMBINATIONS = [f"{category}_{quality}" for category, quality in product(CATEGORIES, QUALITIES)]
        self.cq_pattern = re.compile("|".join(re.escape(combo) for combo in CATEGORY_QUALITY_COMBINATIONS))


    def get_dirs(self) -> tuple[str, str, str]:
        return self.lora_model_dir, self.lora_png_dir, self.output_dir


    # def _initialize_directories(self) -> None:
    #     os.makedirs(self.lora_model_dir, exist_ok=True)
    #     os.makedirs(self.lora_png_dir, exist_ok=True)
    #     os.makedirs(self.output_dir, exist_ok=True)


    def build_png_dictionary(self) -> dict[str, dict[str, list]]:
        """Create an organized dictionary of png directories with structure category:quality:[(lora_name, lora_path)]."""
        png_directory_dict = {}
        for folder in os.listdir(self.lora_png_dir):
            quality = self.get_directory_quality(folder)
            if not quality:
                continue
            category = self.get_directory_category(folder)
            if not category:
                continue
            png_directory_dict.setdefault(category, {}).setdefault(quality, [])
            folder_path = os.path.join(self.lora_png_dir, folder)
            for lora_png_directory in os.listdir(folder_path):
                lora_name, lora_category = self.get_lora_name_and_category_from_png_directory(lora_png_directory)
                if not lora_name:
                    continue
                absolute_path = os.path.normpath(os.path.join(folder_path, lora_png_directory))
                png_directory_dict[category][quality].append((lora_name, absolute_path))
        return png_directory_dict


    def get_lora_png_data(self):
        """Builds a dictionary of PNG directories organized by category and quality."""
        png_data = {}
        for dirpath, dirnames, filenames in os.walk(self.lora_png_dir):
            for dirname in dirnames:
                quality = self.get_directory_quality(dirname)
                if not quality:
                    continue
                category = self.get_directory_category(dirname)
                if not category:
                    continue
                dir_path = os.path.join(dirpath, dirname)
                for subdirectory in os.listdir(dir_path):
                    lora_name, lora_category = self.get_lora_name_and_category_from_png_directory(subdirectory)
                    if lora_name and lora_category:
                        png_path = os.path.join(dir_path, subdirectory)
                        png_data.setdefault(lora_category, {}).setdefault(quality, []).append((lora_name, png_path))
        return png_data


    def build_lora_dictionary(self) -> dict[str, dict[str, list]]:
        """Create an organized dictionary of loras with structure category:quality:[(lora_name, lora_path), ...]"""
        lora_model_dict = {}
        for folder in os.listdir(self.lora_model_dir):
            quality = self.get_directory_quality(folder)
            if not quality:
                continue
            category = self.get_directory_category(folder)
            if not category:
                continue
            lora_model_dict.setdefault(category, {}).setdefault(quality, [])
            folder_path = os.path.join(self.lora_model_dir, folder)
            for file in os.listdir(folder_path):
                if file.endswith(".safetensors"):
                    lora_name = self.get_lora_name_from_filepath(file)
                    if not lora_name:
                        continue
                    absolute_path = os.path.normpath(os.path.join(folder_path, file))
                    lora_model_dict[category][quality].append((lora_name, absolute_path))
        return lora_model_dict


    def get_directory_category(self, subdirectory_name: str) -> str:
        """Function to get the category from a lora or png directory name.\n
        E.g., "S:/Loras/Attire_Good" -> "Good" OR "S:/PNGs/good" -> "Good"."""
        # if subdirectory_name[:2] == "__": # Ignore folders that start with double underscore
        #     return False
        category_map = {
            "attire": "Attire",
            "character": "Character",
            "concept": "Concept",
            "style": "Style",
        }

        base_name = os.path.basename(subdirectory_name.strip("_"))
        category = base_name.split("_")[0].lower()
        return category_map.get(category, None)


    def get_directory_quality(self, subdirectory_name: str) -> str:
        """Function to get the quality from a lora or png directory name.\n
        E.g., "S:/Loras/Attire_Good" -> "Good" OR "S:/PNGs/good" -> "Good"."""
        # if subdirectory_name[:2] == "__": # Ignore folders that start with double underscore
        #     return False
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
        }

        base_name = os.path.basename(subdirectory_name.strip("_"))
        quality = base_name.split("_")[-1].lower()
        return quality_map.get(quality, None)


    @staticmethod
    def get_lora_name_from_filepath(filepath: str) -> str:
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
        elif "FindForgetYou_v2_" in base_name:
            if ".png" in filepath:
                base_path = os.path.dirname(filepath.strip("_"))
                base_name = os.path.split(base_path)[-1]
            lora_name = base_name.replace("FindForgetYou_v2_", "").replace("_TestCards", "")
            return lora_name
        return False


    @staticmethod
    def get_path_by_lora_name(dictionary, lora_name) -> str:
        """Traverse the dictionary and find the matching Lora name."""
        for _category, qualities in dictionary.items():
            for _quality, loras in qualities.items():
                for lora in loras:
                    if lora[0] == lora_name:
                        return lora[1]
        return "None"


    @staticmethod
    def get_lora_name_and_category_from_png_directory(subdirectory_name: str) -> tuple:
        """Get the lora name and category from the png directory name.\n
        E.g., "FindForgetYou_v2_Slavic_Dress_Attire_TestCards/FindForgetYou_v2_Slavic_Dress_Attire_TestCards_00002.png" -> (Slavic_Dress, Attire)."""
        # if subdirectory_name[:2] == "__": # Ignore folders that start with double underscore
        #     return False
        match = PNG_DIRECTORY_PATTERN.search(subdirectory_name.replace("_TestCards",""))
        if match:
            lora_name = match.group(1)
            split = lora_name.split("_")
            category = split.pop()
            return lora_name, category
        return False, False


    def get_quality_from_filepath(self, filepath: str) -> str:
        """Function to get the quality from directory or safetensors/png files.\n
        E.g., "PONY/Attire_Good/Pony_XL_Slavic_Dress_Attire.safetensors" -> "Good"
        "X:\CardArchive\LoraCards\Attire_Scoring\FindForgetYou_v2_Slavic_Dress_Attire_TestCards" -> "Good"
        "X:\CardArchive\LoraCards\Attire_Scoring\FindForgetYou_v2_Slavic_Dress_Attire_TestCards\FindForgetYou_v2_Slavic_Dress_Attire_TestCards_00001.png" -> "Good".
        """
        return self.cq_pattern(filepath)


