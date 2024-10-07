import os
import logging
logger = logging.getLogger(__name__)
import shutil
from helpers import *

ROOT_DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))




class ActionHandler:
    """Class to hold various functions that perform actions (file movement, name changing, etc) based on data returned by InfoHandler class.
    
    move(soure_path, destination_path)
    organize_png_directories_by_lora_directory(parent_directory, png_dict, lora_dict)
    log_dicts(png_dict, lora_dict)
    move_scored_loras_to_intermediary(quality_string)
"""
    
    def __init__(self, config=None):
        self.config_data = config
        self.lora_png_dir = self.get_setting("lora_png_dir")
        self.lora_dir = self.get_setting("lora_dir")

    def get_setting(self, setting):
        return self.config_data.get(setting)
    

    def log_dicts(self, png_dict, lora_dict) -> None:
        lora_log_file_path = os.path.splitext(os.path.abspath(__file__))[0] + "_lora_dict.log"
        png_log_file_path = os.path.splitext(os.path.abspath(__file__))[0] + "_png_dict.log"

        with open(lora_log_file_path,"w") as f:
            f.write(json.dumps(lora_dict,indent=2))
        with open(png_log_file_path,"w") as f:
            f.write(json.dumps(png_dict,indent=2))


    def move(self, source_path, destination_path) -> None:
        # Check if source exists
        if not os.path.exists(source_path):
            raise ValueError(f"Source path not found: {source_path}")
        
        # Determine if destination is a directory
        dest_is_dir = os.path.isdir(destination_path)
        dest_exists = os.path.exists(destination_path)

        # Handle destination path
        if dest_exists:
            if dest_is_dir:
                # Move source into destination directory
                target_path = os.path.join(destination_path, os.path.basename(source_path))
                if os.path.exists(target_path):
                    logging.debug(f"Move failed! Target path already exists: {target_path}")
                    return
            else:
                logging.debug("Move failed! Destination file already exists: %s", destination_path)
                return
        else:
            # Create parent directories if they don't exist
            parent_dir = os.path.dirname(destination_path) or '.'
            os.makedirs(parent_dir, exist_ok=True)
            target_path = destination_path

        try:
            shutil.move(source_path, target_path)
            logging.debug("Successfully moved %s to %s", source_path, target_path)
        except Exception as e:
            logging.error("Error moving file: %s", e, exc_info=1,  stack_info=True)
            raise


    def move_all_files(self, source_directory, destination_directory):
        os.makedirs(destination_directory, exist_ok=True)

        # Iterate over all files in the source directory
        for filename in os.listdir(source_directory):
            # Construct full file path
            src_file_path = os.path.join(source_directory, filename)
            dst_file_path = os.path.join(destination_directory, filename)

            # Check if it is a file (not a directory)
            if os.path.isfile(src_file_path):
                # Move the file
                shutil.move(src_file_path, dst_file_path)


    def initialize_lora_png_directories(self):
        logger.info("Initializing Lora png directories.")
        self.initialize_directories(self.lora_png_dir)


    def initialize_lora_tensor_directories(self):
        logger.info("Initializing Lora tensor directories.")
        self.initialize_directories(self.lora_dir)


    def initialize_directories(self, parent_dir):
        if not os.path.exists(parent_dir):
            try:
                os.makedirs(parent_dir)
                logger.info("Created %s directory.", parent_dir)
            except Exception as e:
                logger.error("Error creating %s directory: %s", parent_dir, e, exc_info=1, stack_info=True)

        for category in CATEGORIES:
            for quality in QUALITIES:
                dir_name = f"{category}_{quality}"
                dir_path = os.path.join(parent_dir, dir_name)
                if not os.path.exists(dir_path):
                    try:
                        os.mkdir(dir_path)
                        logger.info("Created %s directory.", dir_name)
                    except Exception as e:
                        logger.error("Error creating %s directory: %s", dir_name, e, exc_info=1, stack_info=True)


    def organize_png_directories_by_lora_directory(self, parent_directory, png_dict, lora_dict) -> None:
        """Organizes PNG directories to match the structure of Lora directories."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        for folder in os.listdir(parent_directory):
            png_info = get_png_directory_lora_name_and_category(folder)
            if not png_info:
                continue

            lora_name, category = png_info
            found = False
            for category, qualities in png_dict.items():
                for quality, png_entries in qualities.items():
                    target_dir = os.path.join(self.output_dir, f"{category}_{quality}")
                    os.makedirs(target_dir, exist_ok=True)
                    for lora_name, png_path in png_entries:
                        dest_path = os.path.join(target_dir, os.path.basename(png_path))
                        if not os.path.exists(dest_path):
                            try:
                                shutil.copytree(png_path, dest_path)
                                logger.info(f"Copied {png_path} to {dest_path}")
                            except Exception as e:
                                logger.error(f"Error copying directory: {e}")

            if not found:
                print(f"Warning: No matching safetensor found for PNG directory {folder}, {lora_name},{category}/{quality}")


    def move_loras_to_intermediary_by_png_directory(self, png_dict, lora_dict, string_pattern, output_directory) -> None:
        """Based on PNG directories in the directory name specified by string_pattern, move matching loras to the output folder."""
        png_tuples = patch_sub_lists(png_dict, string_pattern)
        logger.debug(json.dumps(lora_dict, indent=2))

        for png_tuple in png_tuples:
            lora_name, png_dir_path = png_tuple