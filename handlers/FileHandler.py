"""If it IO's, here it goes."""
import os
import logging
import json
import shutil
import subprocess
import re

from helpers import CATEGORIES, QUALITIES, ROOT_DIRECTORY
from handlers.CommandHandler import stack, FileMoveCommand
from handlers import DataStoreInterface#, CommandHandler
logger = logging.getLogger(__name__)


class FileHandler(DataStoreInterface):
    """
    Container for various functions that perform file actions.

    Methods:
        log_dicts(png_dict, lora_dict=None, ckpt_dict=None) -> None:
            Print dictionaries to file for review.
        move(source_path: str, destination_path: str) -> None:
            Move file or directory from source to destination.
        move_all_files(source_dir: str, destination_dir: str) -> None:
            Move all files within a source directory to a destination directory
        move_all_files(source_dir: str, destination_dir: str) -> None:
            Move all files within a source directory to a destination directory
        initialize_lora_directories() -> None:
            Create lora model and png subdirectories.

    """

#region Setup

    def __init__(self, config_data: dict = None) -> None:
        self.lora_model_dir = config_data.get('lora_model_dir')
        self.lora_png_dir = config_data.get('lora_png_dir')
        self.model_dict_path = config_data.get("model_dict_path")
        self.output_dir = config_data.get('output_dir')


    def initialize_lora_directories(self) -> None:
        """Create lora subdirectories."""
        #logger.info("Initializing Lora png directories.")
        self._initialize_lora_directory(self.lora_png_dir)
        self._initialize_lora_directory(self.lora_model_dir)


    def _initialize_lora_directory(self, parent_dir: str) -> None:
        """Create subdirectories by category and quality."""
        if not os.path.exists(parent_dir):
            try:
                os.makedirs(parent_dir)
                #logger.info("Created %s directory.", parent_dir)
            except Exception as e:
                logger.exception("Error creating %s directory: %s", parent_dir, e, exc_info=1, stack_info=True)

        for category in CATEGORIES:
            for quality in QUALITIES:
                dir_name = f"{category}_{quality}"
                dir_path = os.path.join(parent_dir, dir_name)
                if not os.path.exists(dir_path):
                    try:
                        os.mkdir(dir_path)
                        #logger.info("Created %s directory.", dir_name)
                    except Exception as e:
                        logger.exception("Error creating %s directory: %s", dir_name, e, exc_info=1, stack_info=True)


#region Interface Methods
    def load_data(self):
        return self.load_json_file(self.model_dict_path)

    def save_data(self, data: dict) -> None:
        self.save_json_file(self.model_dict_path, data)



#region Class methods
    def log_dicts(self, lora_dict, ckpt_dict=None) -> None:
        """Print dictionaries to file for review."""
        png_log_file_path = os.path.splitext(os.path.abspath(__file__))[0] + "_lora_dict.log"
        with open(png_log_file_path,"w") as f:
            f.write(json.dumps(lora_dict, indent=2))
        if ckpt_dict:
            ckpt_log_file_path = os.path.splitext(os.path.abspath(__file__))[0] + "_ckpt_dict.log"
            with open(ckpt_log_file_path,"w") as f:
                f.write(json.dumps(ckpt_dict, indent=2))


    @staticmethod
    def move(source_path, destination_path, quiet=True) -> None:
        """Move file or directory from source to destination."""
        mv_cmd = FileMoveCommand(source_path, destination_path, quiet)
        result = mv_cmd.execute()
        if result:
            stack.push(mv_cmd)
            return True
        return False

    @staticmethod
    def undo_move() -> None:
        """Undo last file movement."""
        stack.undo()


    @staticmethod
    def move_all_files(source_dir: str, destination_dir: str) -> None:
        """Move all files within a source directory to a destination directory."""
        os.makedirs(destination_dir, exist_ok=True)
        for filename in os.listdir(source_dir):
            # Construct full file path
            src_file_path = os.path.join(source_dir, filename)
            dst_file_path = os.path.join(destination_dir, filename)
            # Ignore sub directories
            if os.path.isfile(src_file_path):
                shutil.move(src_file_path, dst_file_path)


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
    def save_json_file(file: str, data: dict|str, relative_path: bool=True, preserve_string: bool=False):
        """Save a dictionary or string to a JSON file, creating directories if needed."""
        if relative_path:
            filepath = os.path.join(os.path.dirname(os.path.realpath(ROOT_DIRECTORY)), file)
        else:
            filepath = file
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='UTF-8') as file:
            if not preserve_string:
                json.dump(data, file, sort_keys=False, indent=2, separators=(",", ": "))
            else:
                file.write(str(data))
