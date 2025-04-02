import logging
import os
import re
import json

from dataclasses import is_dataclass
from itertools import product

from _dataclasses import ModelEntry, DuplicateInfo
from helpers import CKPT_BASE_STRING, LORA_BASE_STRING, CKPT_BASES, LORA_BASES, LORA_CATEGORIES, LORA_QUALITIES, CKPT_CATEGORIES, CKPT_QUALITIES


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


class InfoHandler:
    """ """

    # region Init
    def __init__(self, config_data: dict = None) -> None:
        self.lora_model_dir: str = None
        self.lora_png_dir: str = None
        self.ckpt_model_dir: str = None
        self.ckpt_png_dir: str = None
        self.output_dir: str = None
        self.everything_dir: str = None
        self.category_quality_combinations: list = [
            f"{category}_{quality}" for category, quality in product(LORA_CATEGORIES, LORA_QUALITIES)
        ]
        self.cat_qual_pattern = self.init_regex_pattern(self.category_quality_combinations)
        self._init_dirs(config_data)

    def get_dirs(self) -> tuple[str, str, str]:
        return self.lora_model_dir, self.lora_png_dir, self.output_dir

    def _init_dirs(self, config_data: dict):
        self.lora_model_dir: str = config_data.get("lora_model_dir")
        self.lora_png_dir: str = config_data.get("lora_png_dir")
        self.ckpt_model_dir: str = config_data.get("ckpt_model_dir")
        self.ckpt_png_dir: str = config_data.get("ckpt_png_dir")
        self.output_dir: str = config_data.get("output_dir")
        self.everything_dir: str = config_data.get("everything_dir")

    # region Public Utils

    def get_unified_dictionary(self, lora_dict=None, ckpt_dict=None):
        """Create a unified dictionary of ckpts AND loras with all available information, merging entries and tracking duplicates."""
        if not lora_dict:
            lora_dict = self.get_unified_lora_dictionary()
        if not ckpt_dict:
            ckpt_dict = self.get_unified_ckpt_dictionary()
        unified_dict = {"Lora": lora_dict, "Ckpt": ckpt_dict}
        return unified_dict

    def get_unified_ckpt_dictionary(self, ckpt_name_data=None) -> dict:
        """Create a unified dictionary of ckpts with all available information, merging entries and tracking duplicates."""
        if not ckpt_name_data:
            model_dict = self.build_ckpt_model_dictionary()
            png_dict = self.build_ckpt_png_dictionary()
            ckpt_name_data = self.collect_model_name_data(model_dict, png_dict)
        unified_ckpt_dict = self._build_unified_dict(ckpt_name_data)
        self._cleanup_unified_dict(unified_ckpt_dict)
        return unified_ckpt_dict

    def get_unified_lora_dictionary(self, lora_name_data=None) -> dict:
        """Create a unified dictionary of loras with all available information, merging entries and tracking duplicates."""
        if not lora_name_data:
            model_dict = self.build_lora_model_dictionary()
            png_dict = self.build_lora_png_dictionary()
            lora_name_data = self.collect_model_name_data(model_dict, png_dict)
        unified_lora_dict = self._build_unified_dict(lora_name_data)
        self._cleanup_unified_dict(unified_lora_dict)
        return unified_lora_dict

    def collect_model_name_data(self, model_dict, png_dict) -> dict:
        """Collect data from model and png dictionaries into a unified mapping."""
        model_name_data = {}
        for category, qualities in model_dict.items():
            for quality, models in qualities.items():
                for model_name, model_path in models.items():
                    model_name_data = self._update_model_entry(
                        model_name_data,
                        model_name,
                        model_path=model_path,
                        png_path=None,
                        category=category,
                        quality=quality,
                    )
        for category, qualities in png_dict.items():
            for quality, pngs in qualities.items():
                for model_name, png_path in pngs.items():
                    model_name_data = self._update_model_entry(
                        model_name_data,
                        model_name,
                        model_path=None,
                        png_path=png_path,
                        category=category,
                        quality=quality,
                    )
        return model_name_data

    def _update_model_entry(self, model_name_data, model_name, model_path, png_path, category, quality) -> dict:
        """Update or create an entry for a model_name in the model_name_data mapping."""
        if model_name not in model_name_data:
            model_name_data[model_name] = {
                "model_path": model_path,
                "png_path": png_path,
                "category": category,
                "quality": quality,
                "duplicates": [],
            }
        else:
            entry = model_name_data[model_name]
            # Merge model_path
            if model_path and entry["model_path"] is None:
                entry["model_path"] = model_path
                entry["category"] = category
                entry["quality"] = quality
            elif model_path and entry["model_path"] is not None:
                self._add_or_update_duplicate(
                    entry["duplicates"],
                    category,
                    quality,
                    has_model=True,
                    has_png=False,
                )
            # Merge png_path
            if png_path and entry["png_path"] is None:
                entry["png_path"] = png_path
                if entry["model_path"] is None:
                    entry["category"] = category
                    entry["quality"] = quality
            elif png_path and entry["png_path"] is not None:
                self._add_or_update_duplicate(
                    entry["duplicates"],
                    category,
                    quality,
                    has_model=False,
                    has_png=True,
                )
        return model_name_data

    def _add_or_update_duplicate(self, duplicates, category, quality, has_model, has_png):
        """Add a new duplicate or update an existing one based on category and quality."""
        for dup in duplicates:
            if dup.category == category and dup.quality == quality:
                # Update existing duplicate
                dup.has_model = dup.has_model or has_model
                dup.has_png = dup.has_png or has_png
                return
        # Add new duplicate if not found
        duplicates.append(DuplicateInfo(category=category, quality=quality, has_model=has_model, has_png=has_png))

    def _build_unified_dict(self, model_name_data) -> dict:
        """Construct the unified dictionary from the model_name_data mapping."""
        unified_dict = {}
        for model_name, data in model_name_data.items():
            category = data["category"]
            quality = data["quality"]
            if category not in unified_dict:
                unified_dict[category] = {}
            if quality not in unified_dict[category]:
                unified_dict[category][quality] = {}
            unified_dict[category][quality][model_name] = ModelEntry(
                model_path=data["model_path"],
                png_path=data["png_path"],
                duplicates=data["duplicates"],
            )
        return unified_dict

    def _cleanup_unified_dict(self, unified_dict):
        """Remove empty qualities and categories from the unified dictionary."""
        for category in list(unified_dict.keys()):
            for quality in list(unified_dict[category].keys()):
                if not unified_dict[category][quality]:
                    del unified_dict[category][quality]
            if not unified_dict[category]:
                del unified_dict[category]

    def reunify_lora_dictionary(self, dirty_dict) -> dict[str, dict[str, dict[str, tuple[str | None, str | None]]]]:
        """Not factored to match current unified_dict, but this is intended to be a lighter weight function to
        organize an already existing dictionary rather than creating a new one."""
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
                            unified_entry[1] or png_path,  # Keep the existing png_path or use the new one
                        ]
                        unified_dict[existing_category][existing_quality][lora_name] = unified_entry
                    else:
                        # First time seeing this lora_name
                        unified_dict[category][quality][lora_name] = [
                            model_path,
                            png_path,
                        ]

                        # If this lora_name has a lora file, prioritize this category/quality
                        if model_path:
                            seen_loras[lora_name] = (category, quality)

        # Clean up empty qualities
        for category in list(unified_dict.keys()):
            for quality in list(unified_dict[category].keys()):
                if not unified_dict[category][quality]:
                    del unified_dict[category][quality]

        return unified_dict

    def build_lora_png_dictionary(self) -> dict[str, dict[str, dict[str, str]]]:
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
                lora_name = self._get_lora_name_from_png_directory(lora_png_directory)
                if not lora_name:
                    continue
                absolute_path = os.path.normpath(os.path.join(folder_path, lora_png_directory))
                png_directory_dict[category][quality][lora_name] = absolute_path
        return self.sort_built_dictionary(png_directory_dict)

    def build_lora_model_dictionary(self) -> dict[str, dict[str, dict[str, str]]]:
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

    def build_ckpt_png_dictionary(self) -> dict[str, dict[str, dict[str, str]]]:
        """Create an organized dictionary of png directories with structure category:quality:[(ckpt_name, ckpt_path)]."""
        png_directory_dict = {}
        for folder in os.listdir(self.ckpt_png_dir):
            quality = self._get_directory_quality(folder)
            if not quality:
                continue
            category = self._get_directory_category(folder)
            if not category:
                continue
            png_directory_dict.setdefault(category, {}).setdefault(quality, {})
            folder_path = os.path.join(self.ckpt_png_dir, folder)
            for ckpt_png_directory in os.listdir(folder_path):
                ckpt_name = self._get_ckpt_name_from_png_directory(ckpt_png_directory)
                if not ckpt_name:
                    continue
                absolute_path = os.path.normpath(os.path.join(folder_path, ckpt_png_directory))
                png_directory_dict[category][quality][ckpt_name] = absolute_path
        return self.sort_built_dictionary(png_directory_dict)

    def build_ckpt_model_dictionary(self) -> dict[str, dict[str, dict[str, str]]]:
        """Create an organized dictionary of ckpts with structure category:quality:[(ckpt_name, ckpt_path), ...]"""
        ckpt_model_dict = {}
        for folder in os.listdir(self.ckpt_model_dir):
            quality = self._get_directory_quality(folder)
            if not quality:
                continue
            category = self._get_directory_category(folder)
            if not category:
                continue
            ckpt_model_dict.setdefault(category, {}).setdefault(quality, {})
            folder_path = os.path.join(self.ckpt_model_dir, folder)
            for file in os.listdir(folder_path):
                if file.endswith(".safetensors"):
                    ckpt_name = self._get_ckpt_name_from_model_filepath(file)
                    if not ckpt_name:
                        continue
                    absolute_path = os.path.normpath(os.path.join(folder_path, file))
                    ckpt_model_dict[category][quality][ckpt_name] = absolute_path
        return self.sort_built_dictionary(ckpt_model_dict)

    def find_hanging_png_directoriesOLD(self):
        lora_dict = self.build_lora_model_dictionary()
        png_dict = self.build_lora_png_dictionary()
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

    def get_paths_by_lora_name(self, dictionary, lora_name) -> str:
        """Traverse the dictionary and find the matching Lora name."""
        for _category, qualities in dictionary.items():
            for _quality, loras in qualities.items():
                for lora_key, (lora_model_path, lora_png_path) in loras.items():
                    if lora_key == lora_name:
                        return lora_model_path, lora_png_path
        return "None"

    def init_regex_pattern(self, category_quality_combinations):
        return re.compile("|".join(category_quality_combinations))

    def sort_built_dictionary(self, built_dictionary: dict) -> dict:
        """Sort the dictionary by category and quality keys."""
        sorted_lora_directory_dict = {
            category: {
                quality: dict(sorted(loras.items()))
                for quality, loras in sorted(
                    qualities.items(),
                    key=lambda q: self._lora_quality_sort_key(q[0]),
                    reverse=True,
                )
            }
            for category, qualities in sorted(
                built_dictionary.items(),
                key=lambda q: self._lora_category_sort_key(q[0]),
                reverse=True,
            )
        }
        return sorted_lora_directory_dict

    def _lora_category_sort_key(self, category):
        """Use the index in LORA_CATEGORIES for sorting; if category is not found, assign a high index."""
        return LORA_CATEGORIES.index(category) if category in LORA_CATEGORIES else len(LORA_CATEGORIES)

    def _lora_quality_sort_key(self, quality):
        """Use the index in LORA_QUALITIES for sorting; if quality is not found, assign a high index."""
        return LORA_QUALITIES.index(quality) if quality in LORA_QUALITIES else len(LORA_QUALITIES)

    def _ckpt_category_sort_key(self, category):
        """Use the index in CKPT_CATEGORIES for sorting; if category is not found, assign a high index."""
        return CKPT_CATEGORIES.index(category) if category in CKPT_CATEGORIES else len(CKPT_CATEGORIES)

    def _ckpt_quality_sort_key(self, quality):
        """Use the index in CKPT_QUALITIES for sorting; if quality is not found, assign a high index."""
        return CKPT_QUALITIES.index(quality) if quality in CKPT_QUALITIES else len(CKPT_QUALITIES)

    def _get_directory_category(self, subdirectory_name: str) -> str:
        """Function to get the category from a lora or png directory name.\n
        E.g., "S:/Loras/Attire_Good" -> "Good" OR "S:/PNGs/good" -> "Good"."""
        category_map = {
            "attire": "Attire",
            "character": "Character",
            "concept": "Concept",
            "style": "Style",
            "drawn": "Drawn",
            "semi": "Semi",
            "real": "Real",
        }
        base_name = os.path.basename(subdirectory_name.strip("_"))
        category = base_name.split("_")[0].lower()
        return category_map.get(category, None)

    def _get_directory_quality(self, subdirectory_name: str) -> str:
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

    def _get_lora_name_from_model_filepath(self, filepath: str) -> str:
        """Function to get the lora name from directory or safetensors/png files.\n
        E.g., "PONY/Attire_Good/Pony_XL_Slavic_Dress_Attire.safetensors" -> "Slavic_Dress_Attire"
        "X:\CardArchive\LoraCards\Attire_Scoring\FindForgetYou_v2_Slavic_Dress_Attire_TestCards" -> "Slavic_Dress_Attire".
        "X:\CardArchive\LoraCards\Attire_Scoring\FindForgetYou_v2_Slavic_Dress_Attire_TestCards\FindForgetYou_v2_Slavic_Dress_Attire_TestCards_00001.png -> (Slavic_Dress, Attire)".
        """
        base_path = os.path.splitext(filepath.strip("_"))[0]
        base_name = os.path.split(base_path)[-1]
        if ".safetensors" in filepath:
            pattern = r"^(?:" + CKPT_BASE_STRING + r")(.*)"
            match = re.search(pattern, base_name)
            if match:
                lora_name = match.group(1)
                for base in CKPT_BASES[1:]:
                    if base in base_name:
                        lora_name = base + lora_name
                return lora_name
            else:
                logger.debug(f"{base_name} is not formatted properly. Missing 'Pony_XL_'")
        elif any(base in base_name for base in LORA_BASES):
            if ".png" in filepath:
                base_path = os.path.dirname(filepath.strip("_"))
                base_name = os.path.split(base_path)[-1]
            #lora_name = base_name.replace("FindForgetYou_v2_", "").replace("ILL_WAIAniNSFW_v11_", "ILL_").replace("_TestCards", "")
            lora_name = re.sub(LORA_BASE_STRING, "", base_name).replace("_TestCards", "")
            for base in LORA_BASES:
                if base in base_name:
                    lora_name = base + lora_name
            return lora_name
        return False

    def _get_ckpt_name_from_model_filepath(self, filepath: str) -> str:
        """Function to get the ckpt name from directory or safetensors/png files.\n
        E.g., "PONY/Drawn_Scoring/Pony_XL_PonyV6_Ckpt.safetensors" -> "PonyV6"
        "X:\CardArchive\CkptCards\Drawn_Scoring\PonyV6" -> "PonyV6".
        "X:\CardArchive\CkptCards\Drawn_Scoring\PonyV6\PonyV6_00001.png -> "PonyV6".
        """
        base_path = os.path.splitext(filepath.strip("_"))[0]
        base_name = os.path.split(base_path)[-1]
        if ".safetensors" in filepath:
            #pattern = r"(?:Pony_XL_|ILL_)(.*)"
            pattern = r"^(?:" + CKPT_BASE_STRING + r")(.*)"
            match = re.search(pattern, base_name)
            if match:
                #ckpt_name = match.group(1) if "ILL_" not in match.group(1) else match.group(0)
                ckpt_name = match.group(1)
                for base in CKPT_BASES[1:]:
                    if base in base_name:
                        ckpt_name = base + ckpt_name
                ckpt_name = ckpt_name.replace("_TestCards", "").replace("_Ckpt", "")
                return ckpt_name
            else:
                logger.debug(f"{base_name} is not formatted properly. Missing 'Pony_XL_', 'ILL_' or '_Ckpt'")
        else:
            #ckpt_name = base_name.replace("Pony_XL_", "").replace("_TestCards", "").replace("_Ckpt", "")
            ckpt_name = re.sub(CKPT_BASE_STRING, "", base_name).replace("_TestCards", "").replace("_Ckpt", "")
            for base in CKPT_BASES[1:]:
                if base in base_name:
                    ckpt_name = base + ckpt_name
            return ckpt_name
        return False

    def _get_lora_name_from_png_directory(self, subdirectory_name: str) -> tuple:
        """Get the lora name and category from the png directory name.\n
        E.g., "FindForgetYou_v2_Slavic_Dress_Attire_TestCards" -> (Slavic_Dress, Attire).
        """
        pattern = r"^(?:" + LORA_BASE_STRING + r")(.*)"
        #pattern = r"(?:FindForgetYou_v2_|ILL_WAIAniNSFW_v11_)(.*)"
        match = re.search(pattern, subdirectory_name.replace("_TestCards", ""))
        if match:
            lora_name = match.group(1)
            return lora_name
        return False

    def _get_ckpt_name_from_png_directory(self, subdirectory_name: str) -> tuple:
        """Get the ckpt name and category from the png directory name.\n
        E.g., "PonyV6" -> "PonyV6".
        """
        ckpt_name = subdirectory_name
        return ckpt_name

    @staticmethod
    def initialize_dictionary_template():
        return {category: {quality: {} for quality in LORA_QUALITIES} for category in LORA_CATEGORIES}

    @staticmethod
    def print_unified_dict(unified_dict):
        """Recursively process and pretty print unified_dict, avoiding double-encoding."""

        def process_element(element):
            if is_dataclass(element):
                # Convert dataclass to dictionary
                return {key: process_element(value) for key, value in element.to_dict().items()}
            elif isinstance(element, dict):
                # Process dictionaries
                return {key: process_element(value) for key, value in element.items()}
            elif isinstance(element, list):
                # Process lists
                return [process_element(item) for item in element]
            else:
                # Base case for other types
                return element

        processed_dict = process_element(unified_dict)

        return json.dumps(processed_dict, indent=2)

    @staticmethod
    def serialize_output(output):
        """Recursively serialize dataclass instances to dictionaries."""
        if isinstance(output, dict):
            return {key: InfoHandler.serialize_output(value) for key, value in output.items()}
        elif isinstance(output, list):
            return [InfoHandler.serialize_output(item) for item in output]
        elif hasattr(output, "to_dict"):
            return output.to_dict()
        else:
            return output
