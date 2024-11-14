import os
import logging
import json
import shutil
import subprocess
import shlex
import re

from helpers import *

ROOT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

logger = logging.getLogger(__name__)

class FileHandler:
    """
    Container for various functions that perform file actions.

    Methods
    -------
    log_dicts(png_dict, lora_dict=None, ckpt_dict=None) -> None:
        Print dictionaries to file for review.\n
    move(source_path: str, destination_path: str) -> None:
        Move file or directory from source to destination.\n
    move_all_files(source_dir: str, destination_dir: str) -> None:
        Move all files within a source directory to a destination directory\n
    move_all_files(source_dir: str, destination_dir: str) -> None:
        Move all files within a source directory to a destination directory\n
    initialize_lora_png_directories() -> None:
        Create lora png subdirectories.\n
    initialize_lora_tensor_directories() -> None:
        Create lora model subdirectories.\n
    """

    def __init__(self, config_data: dict = None) -> None:
        self.lora_model_dir = config_data.get('lora_model_dir')
        self.lora_png_dir = config_data.get('lora_png_dir')
        self.everything_path = config_data.get('everything_path')
        self.output_dir = config_data.get('output_dir')


    def log_dicts(self, png_dict, lora_dict=None, ckpt_dict=None) -> None:
        """Print dictionaries to file for review."""
        png_log_file_path = os.path.splitext(os.path.abspath(__file__))[0] + "_png_dict.log"
        with open(png_log_file_path,"w") as f:
            f.write(json.dumps(png_dict, indent=2))
        if lora_dict:
            lora_log_file_path = os.path.splitext(os.path.abspath(__file__))[0] + "_lora_dict.log"
            with open(lora_log_file_path,"w") as f:
                f.write(json.dumps(lora_dict, indent=2))
        if ckpt_dict:
            ckpt_log_file_path = os.path.splitext(os.path.abspath(__file__))[0] + "_ckpt_dict.log"
            with open(ckpt_log_file_path,"w") as f:
                f.write(json.dumps(ckpt_dict, indent=2))


    def move(self, source_path, destination_path, quiet=True) -> None:
        """Move file or directory from source to destination."""
        if not os.path.exists(source_path):
            raise ValueError(f"File not found: {source_path}")
        if source_path == destination_path:
            logger.debug("Cancel move: %s = %s", source_path, destination_path)
            return
        dest_is_dir = os.path.isdir(destination_path)
        dest_exists = os.path.exists(destination_path)
        if dest_exists:
            if dest_is_dir:
                # Move source into destination directory
                target_path = os.path.join(destination_path, os.path.basename(source_path))
            else:
                logging.debug("Move failed! Destination file already exists: %s", destination_path)
                return
        else:
            parent_dir = os.path.dirname(destination_path) or '.'
            os.makedirs(parent_dir, exist_ok=True)
            target_path = destination_path

        if os.path.exists(target_path):
            logging.debug(f"Move failed! Target path already exists: {target_path}")
            return

        try:
            shutil.move(source_path, target_path)
            if not quiet:
                logging.debug("Successfully moved %s to %s", source_path, target_path)
        except Exception as e:
            logging.exception("Error moving file: %s", e, exc_info=1,  stack_info=True)
            raise


    def move_all_files(self, source_dir: str, destination_dir: str) -> None:
        """Move all files within a source directory to a destination directory."""
        os.makedirs(destination_dir, exist_ok=True)
        for filename in os.listdir(source_dir):
            # Construct full file path
            src_file_path = os.path.join(source_dir, filename)
            dst_file_path = os.path.join(destination_dir, filename)
            # Ignore sub directories
            if os.path.isfile(src_file_path):
                shutil.move(src_file_path, dst_file_path)


    def initialize_lora_png_directories(self) -> None:
        """Create lora png subdirectories."""
        logger.info("Initializing Lora png directories.")
        self._initialize_directories(self.lora_png_dir)


    def initialize_lora_model_directories(self) -> None:
        """Create lora model subdirectories."""
        logger.info("Initializing Lora model directories.")
        self._initialize_directories(self.lora_model_dir)


    def _initialize_directories(self, parent_dir: str) -> None:
        """Create subdirectories by category and quality."""
        if not os.path.exists(parent_dir):
            try:
                os.makedirs(parent_dir)
                logger.info("Created %s directory.", parent_dir)
            except Exception as e:
                logger.exception("Error creating %s directory: %s", parent_dir, e, exc_info=1, stack_info=True)

        for category in CATEGORIES:
            for quality in QUALITIES:
                dir_name = f"{category}_{quality}"
                dir_path = os.path.join(parent_dir, dir_name)
                if not os.path.exists(dir_path):
                    try:
                        os.mkdir(dir_path)
                        logger.info("Created %s directory.", dir_name)
                    except Exception as e:
                        logger.exception("Error creating %s directory: %s", dir_name, e, exc_info=1, stack_info=True)



    def search_with_everything(self, txt):
        if not self.everything_path:
            raise ValueError("Everything path isn't set.")
        if not os.path.exists(self.everything_path):
            raise FileNotFoundError("Everything.exe not found at assigned path.")
        txt = shlex.quote(txt)
        subprocess.Popen(["cmd", "/c", "start", "", self.everything_path, "-search", txt])


    @staticmethod
    def open_to_file(filepath: str) -> None:
        """If filepath is a directory, it opens the directory. If filepath is a file, it opens the parent directory with the file selected."""
        if filepath:
            if os.path.isfile(filepath):
                subprocess.run(['explorer', '/select,', filepath])
                return True
            elif os.path.isdir(filepath):
                subprocess.run(['explorer', filepath])
                return True
        return False


    @staticmethod
    def load_json_file(file: str, default=None, relative_path: bool = True):
        """Reads a json file and returns the json dict, stripping out "//" comments first."""
        if relative_path:
            filepath = os.path.join(os.path.dirname(os.path.realpath(ROOT_DIRECTORY)), file)
        else:
            filepath = file
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='UTF-8') as file:
                config = re.sub(r"(?:^|\s)//.*", "", file.read(), flags=re.MULTILINE)
            return json.loads(config)
        return default


    @staticmethod
    def save_json_file(file: str, data: dict, relative_path: bool=True):
        if relative_path:
            filepath = os.path.join(os.path.dirname(os.path.realpath(ROOT_DIRECTORY)), file)
        else:
            filepath = file
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='UTF-8') as file:
            json.dump(data, file, sort_keys=False, indent=2, separators=(",", ": "))



    def add_to_json_dictionary(self, filepath: str, subdicts: list, relative_path: bool=True) -> dict:
        """Special function to add entries to Ali .json and preserve formatting. Returns updated dictionary.\n\n
    subdicts = [
        {"lora_name_key": {"TRIGGERS": "", "WEIGHT": "", "NEGATIVES": "", "NULLIFIERS": "", "NOTES": ""}},
    ]"""
        ali_dict = self.load_json_file(filepath, relative_path)

        for dictionary in subdicts:
            for key, data in dictionary.items():
                ali_dict[key] = data

        if relative_path:
            filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), filepath)

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        sorted_dict = {key: ali_dict[key] for key in sorted(ali_dict)}

        out_str = "{"
        for k, v in sorted_dict.items():
            out_str += f'\n    "{k}": {json.dumps(v, separators=(", ", ": "))},'

        out_str = out_str[:-1]
        out_str += "\n}"

        with open(filepath, 'w', encoding='UTF-8') as file:
            file.write(out_str)

        return sorted_dict





    # def organize_png_directories_by_lora_directory(self, parent_directory: str, png_dict: str, lora_dict: str) -> None:
    #     """Temporary function to organize PNG directories to match the structure of Lora directories."""
    #     if not os.path.exists(self.output_dir):
    #         os.makedirs(self.output_dir)

    #     for folder in os.listdir(parent_directory):
    #         png_info = get_lora_name_and_category_from_png_directory(folder)
    #         if not png_info:
    #             continue

    #         lora_name, category = png_info
    #         found = False
    #         for category, qualities in png_dict.items():
    #             for quality, png_entries in qualities.items():
    #                 target_dir = os.path.join(self.output_dir, f"{category}_{quality}")
    #                 os.makedirs(target_dir, exist_ok=True)
    #                 for lora_name, png_path in png_entries:
    #                     dest_path = os.path.join(target_dir, os.path.basename(png_path))
    #                     if not os.path.exists(dest_path):
    #                         try:
    #                             shutil.copytree(png_path, dest_path)
    #                             logger.info(f"Copied {png_path} to {dest_path}")
    #                         except Exception as e:
    #                             logger.exception(f"Error copying directory: {e}")

    #         if not found:
    #             print(f"Warning: No matching safetensor found for PNG directory {folder}, {lora_name},{category}/{quality}")


    # def move_loras_to_intermediary_by_png_directory(self, png_dict, lora_dict, string_pattern, output_directory) -> None:
    #     """Based on PNG directories in the directory name specified by string_pattern, move matching loras to the output folder."""
    #     png_tuples = patch_sub_lists(png_dict, string_pattern)
    #     logger.debug(json.dumps(lora_dict, indent=2))

    #     for png_tuple in png_tuples:
    #         lora_name, png_dir_path = png_tuple


