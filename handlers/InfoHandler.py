import logging
import os

logger = logging.getLogger(__name__)

ROOT_DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from helpers import *

class InfoHandler():
    """Class to hold various info gathering tools that return info for the ActionHandler class."""
    def __init__(self, config_data):
        self.lora_dir_path = config_data.get('lora_dir')
        self.lora_png_dir_path = config_data.get('lora_png_dir')
        self.output_dir_path = config_data.get('output_dir')


    def get_dirs(self) -> tuple[str, str, str]:
        return self.lora_dir_path, self.lora_png_dir_path, self.output_dir_path
    




    def build_png_dictionary(self) -> dict[str, dict[str, list]]:
        """Create an organized dictionary of png directories with structure category:quality:[(lora_name, lora_path)]."""
        png_directory_dict = {}
        for quality_folder in os.listdir(self.lora_png_dir_path):
            quality = get_directory_quality(quality_folder)
            if not quality:
                continue

            quality_folder_path = os.path.join(self.lora_png_dir_path, quality_folder)
            for lora_png_directory in os.listdir(quality_folder_path):
                lora_name, category = get_png_directory_lora_name_and_category(lora_png_directory)
                if not lora_name:
                    continue
                absolute_path = os.path.join(quality_folder_path, lora_png_directory)
                png_directory_dict.setdefault(category, {}).setdefault(quality, []).append((lora_name, absolute_path))

        return png_directory_dict
    

    def get_png_data(self):
            """Builds a dictionary of PNG directories organized by category and quality."""
            png_data = {}
            for directory in os.listdir(self.png_dir):
                quality = get_directory_quality(directory)
                if quality:
                    dir_path = os.path.join(self.png_dir, directory)
                    for subdirectory in os.listdir(dir_path):
                        lora_name, category = get_png_directory_lora_name_and_category(subdirectory)
                        if lora_name and category:
                            png_path = os.path.join(dir_path, subdirectory)
                            png_data.setdefault(category, {}).setdefault(quality, []).append((lora_name, png_path))
            return png_data
    

    def build_lora_dictionary(self) -> dict[str, dict[str, list]]:
        """Create an organized dictionary of loras with structure category:quality:[(lora_name, lora_path)]."""
        safetensors_dict = {}
        for folder in os.listdir(self.lora_dir_path):
            folder_info = get_lora_directory_quality_and_category(folder)
            if not folder_info[0]:
                continue

            category, quality = folder_info

            folder_path = os.path.join(self.lora_dir_path, folder)
            for file in os.listdir(folder_path):
                if file.endswith(".safetensors"):
                    lora_name = get_lora_name(file)

                    if not lora_name:
                        continue

                    if category not in safetensors_dict:
                        safetensors_dict[category] = {}
                    if quality not in safetensors_dict[category]:
                        safetensors_dict[category][quality] = []

                    absolute_path = os.path.join(folder_path, file)
                    safetensors_dict[category][quality].append((lora_name, absolute_path))

        return safetensors_dict