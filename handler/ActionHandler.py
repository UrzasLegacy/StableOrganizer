import os
import logging
logger = logging.getLogger(__name__)

ROOT_DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import shutil
from helpers import *


#region ActionHandler
class ActionHandler:
    """Class to hold various functions that perform actions (file movement, name changing, etc) based on data returned by InfoHandler class.
    
    Action Types:
        OrganizePNGs
        MoveScoredLoras: "action_data": {specific: "Good"}
        LogDicts
        MoveFile: "action_data": {file_path: "C:\Beep\Borp.txt", destination_folder: "C:\Boop"}"""
    
    def __init__(self, info_data=None):
        if not info_data:
            raise ValueError("You must provide an InfoHandler dictionary")
        
        config_data = info_data.get("config_data")
        if not config_data:
            raise ValueError("You must provide config data")
        
        action_type = info_data.get("action_type", "")
        if not action_type.strip():
            raise ValueError("You must provide an action type")
        
        self.func_map = {
            "OrganizePNG": self.organize_png_directories_by_lora_directory,
            "MoveScoredLoras": self.move_loras_to_intermediary_by_png_directory,
            "LogDicts": self.log_dicts,
            "MoveFile": self.move,
        }

        if not action_type in self.func_map:
            raise ValueError("Action type does not match an available action function")
        
        self.info_data: dict = info_data
        self.config_data: dict = config_data

        self.action_type: str = self.info_data.get("action_type", "")
        self.action_data: dict = self.info_data.get("action_data", {})

 
 



        print(f"""Lora Directory: {self.get_setting("lora_dir_path")}
PNG Directory: {self.get_setting("png_lora_dir_path")}
Output Directory: {self.get_setting("output_dir_path")}""")

    def get_setting(self, setting):
        return self.config_data.get(setting)

    def act(self):
        """Initiate the ActionHandler object's action. Variable return types."""
        action = self.func_map.get(self.action_type, lambda: False)
        return action()
    
    def log_dicts(self) -> None:
        lora_log_file_path = os.path.splitext(os.path.abspath(__file__))[0] + "_lora_dict.log"
        png_log_file_path = os.path.splitext(os.path.abspath(__file__))[0] + "_png_dict.log"

        dicts = self.data
        if len(dicts) < 2:
            raise ValueError("Dicts missing")
        
        lora_dict, png_dict = dicts

        with open(lora_log_file_path,"w") as f:
            f.write(json.dumps(lora_dict,indent=2))
        with open(png_log_file_path,"w") as f:
            f.write(json.dumps(png_dict,indent=2))

    def move(self, source_path, destination_path) -> None:
        src_exists = os.path.exists(source_path)
        if not src_exists:
            raise ValueError("Source path not found")
        
        src_is_folder = os.path.isdir(source_path)
        src_is_file = os.path.isfile(source_path)
        dest_is_folder = os.path.isdir(destination_path)
        dest_is_file = os.path.isfile(destination_path)
        dest_exists = os.path.exists(destination_path)

        if dest_exists:
            if dest_is_file:
                logger.debug(f"Move failed! Destination path already exists for file: {destination_path}")
                return
            elif dest_is_folder:
                logger.debug("Moving all files in source_directory into destination directory")
                self.move_all_files(source_path, destination_path)
                return
        
        if os.path.isfile(source_path):
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        elif os.path.isdir(source_path):
            os.makedirs(destination_path, exist_ok=True)

        shutil.move(source_path, destination_path)

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

    def organize_png_directories_by_lora_directory(self) -> None:
        """Create a directory hierarchy to match the lora directory and match the png directories to their lora counterpart's position."""
        png_dict = self.data
        output_dir = self.get_setting("output_dir")
        png_lora_dir = self.get_setting("png_lora_dir")

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for folder in os.listdir(png_lora_dir):
            png_info = get_png_directory_lora_name_and_category(folder)
            if not png_info:
                continue

            lora_name, category = png_info
            found = False
            for quality in png_dict.get(category, {}):
                if lora_name in png_dict[category][quality]:
                    dest_dir = os.path.join(self.output_dir_path, f"{category}_{quality}")
                    if not os.path.exists(dest_dir):
                        os.makedirs(dest_dir)
                    #shutil.copytree(os.path.join(self.png_dir_path, folder), os.path.join(dest_dir, folder))
                    found = True
                    break

            if not found:
                print(f"Warning: No matching safetensor found for PNG directory {folder}, {lora_name},{category}/{quality}")

    def move_loras_to_intermediary_by_png_directory(self, png_directory) -> None:
        """Based on PNG directories in the directory name specified by self.specific, move matching loras to the output folder."""
        dicts = self.data

        if len(dicts) < 2:
            raise ValueError("Check info dictionary, must have lora_dict and png_dict")
        lora_dict = dicts[0]
        png_dict = dicts[1]

        if not self.specific:
            raise ValueError("must be specific at the moment")
        
        png_tuples = patch_sub_lists(png_dict, self.specific)
        logger.debug(json.dumps(lora_dict, indent=2))

        for png_tuple in png_tuples:
            lora_name, png_dir_path = png_tuple