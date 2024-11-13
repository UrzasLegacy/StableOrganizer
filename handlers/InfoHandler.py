import logging
import os

from helpers import *


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
        # self._initialize_directories()


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
            quality = get_directory_quality(folder)
            if not quality:
                continue
            category = get_directory_category(folder)
            if not category:
                continue
            png_directory_dict.setdefault(category, {}).setdefault(quality, [])
            folder_path = os.path.join(self.lora_png_dir, folder)
            for lora_png_directory in os.listdir(folder_path):
                lora_name, lora_category = get_png_directory_lora_name_and_category(lora_png_directory)
                if not lora_name:
                    continue
                absolute_path = os.path.normpath(os.path.join(folder_path, lora_png_directory))
                png_directory_dict[category][quality].append((lora_name, absolute_path))
        return png_directory_dict


    def get_lora_png_data(self):
        """Builds a dictionary of PNG directories organized by category and quality."""
        png_data = {}
        for directory in os.listdir(self.lora_png_dir):
            quality = get_directory_quality(directory)
            if quality:
                dir_path = os.path.join(self.png_root_dir, directory)
                for subdirectory in os.listdir(dir_path):
                    lora_name, category = get_png_directory_lora_name_and_category(subdirectory)
                    if lora_name and category:
                        png_path = os.path.join(dir_path, subdirectory)
                        png_data.setdefault(category, {}).setdefault(quality, []).append((lora_name, png_path))
        return png_data


    def build_lora_dictionary(self) -> dict[str, dict[str, list]]:
        """Create an organized dictionary of loras with structure category:quality:[(lora_name, lora_path), ...]"""
        lora_model_dict = {}
        for folder in os.listdir(self.lora_model_dir):
            category, quality = get_lora_directory_quality_and_category(folder)
            if not category or not quality:
                continue
            lora_model_dict.setdefault(category, {}).setdefault(quality, [])
            folder_path = os.path.join(self.lora_model_dir, folder)
            for file in os.listdir(folder_path):
                if file.endswith(".safetensors"):
                    lora_name = get_lora_name(file)
                    if not lora_name:
                        continue
                    absolute_path = os.path.normpath(os.path.join(folder_path, file))
                    lora_model_dict[category][quality].append((lora_name, absolute_path))
        return lora_model_dict