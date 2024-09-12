import os
import logging
logger = logging.getLogger(__name__)

ROOT_DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from helpers import *

#region ACT
class ACT:
    """Class to hold various functions that perform actions (file movement, name changing, etc) based on data returned by INFO class."""
    def __init__(self, action_type="", info_data=None):
        if not action_type.strip():
            raise ValueError("You must provide an action type")
        if not info_data:
            raise ValueError("You must provide an INFO dictionary")
        
        self.func_map = {
            "OrganizePNG": self.organize_png_directories_by_lora_directory,
            "MoveProcessedLoras": self.move_loras_to_intermediary_by_png_directory,
            "LogDicts": self.log_dicts,
        }

        if not action_type in self.func_map:
            raise ValueError("Action type does not match an action function")
        
        self.info_data = info_data
        self.action_type = action_type
        self.lora_dir_path = None
        self.png_dir_path = None
        self.output_dir_path = None
        self.data = None

        dirs = info_data.get("dirs", False)
        if dirs:
            self.lora_dir_path, self.png_dir_path, self.output_dir_path = dirs


        print(f"""Lora Directory: {self.lora_dir_path}
PNG Directory: {self.png_dir_path}
Output Directory: {self.output_dir_path}""")
  
        
        data = info_data.get("data", False)
        if data:
            self.data = data
            print("Data dictionary found")
        else:
            print("Data dictionary missing")

        self.specific = info_data.get("specific", False)
        print(f"Specific: {self.specific}")

    def act(self):
        """Initiate the ACT object's action. Variable return types."""
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

    def organize_png_directories_by_lora_directory(self) -> None:
        """Create a directory hierarchy to match the lora directory and match the png directories to their lora counterpart's position."""
        png_dict = self.data

        if not os.path.exists(self.output_dir_path):
            os.makedirs(self.output_dir_path)

        for folder in os.listdir(self.png_dir_path):
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


    def move_loras_to_intermediary_by_png_directory(self) -> None:
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