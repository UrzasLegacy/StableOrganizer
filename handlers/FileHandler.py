"""If it IO's, here it goes."""
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

#region Init

    def __init__(self, config_data: dict = None) -> None:
        self.lora_model_dir = config_data.get('lora_model_dir')
        self.lora_png_dir = config_data.get('lora_png_dir')
        self.everything_path = config_data.get('everything_path')
        self.model_dictionary_path = config_data.get("model_dictionary_path")
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


    # Public Utils
    def search_with_everything(self, txt):
        """Search txt with external program: Everything."""
        if not self.everything_path:
            raise ValueError("Everything path isn't set.")
        if not os.path.exists(self.everything_path):
            raise FileNotFoundError("Everything.exe not found at assigned path.")
        txt = shlex.quote(txt)
        subprocess.Popen(["cmd", "/c", "start", "", self.everything_path, "-search", txt])


    def validate_root_dictionary(self, root_dictionary=None) -> bool:
        """
        Validates the structure of the root dictionary for required keys and types.

        Parameters:
            root_dictionary (dict, optional): The dictionary to validate. If None, the dictionary is loaded
                                            from the file specified by `self.model_dictionary_path`.

        Returns:
            bool: True if the root dictionary is valid, False otherwise.
        """
        if root_dictionary is None:
            root_dictionary = self.load_json_file(self.model_dictionary_path)
        if not isinstance(root_dictionary, dict) or "lora" not in root_dictionary or "ckpt" not in root_dictionary:
            logger.error(f"Root dictionary is invalid.\n{root_dictionary}")
            return False
        lora_data = root_dictionary.get("lora", {})
        if not isinstance(lora_data, dict) or "hash" not in lora_data or "name" not in lora_data:
            logger.error(f"LoRA dictionary is invalid.\n{lora_data}")
            return False
        ckpt_data = root_dictionary.get("ckpt", {})
        if not isinstance(ckpt_data, dict) or "hash" not in ckpt_data or "name" not in ckpt_data:
            logger.error(f"Ckpt dictionary is invalid.\n{ckpt_data}")
            return False
        return True


    def retrieve_lora_data_by_name(self, root_dictionary=None, lora_key_name: str="") -> tuple:
        """
        Retrieves LoRA model data by its name key from the root dictionary.

        Parameters:
            root_dictionary (dict, optional): The dictionary containing LoRA data. If None, the dictionary
                                            is loaded from the file specified by `self.model_dictionary_path`.
            lora_key_name (str): The name key of the LoRA model to retrieve.

        Returns:
            tuple: A tuple containing the name key and the corresponding model data.
                If the name key is missing, the model data includes an error message.
        """
        if root_dictionary is None:
            root_dictionary = self.load_json_file(self.model_dictionary_path)
        # if not FileHandler.validate_root_dictionary(root_dictionary):
        #     return {"error": "Invalid dictionary"}
        model_data = root_dictionary["lora"]["name"].get(lora_key_name, {"error": "Missing lora_key_name in dictionary"})
        return lora_key_name, model_data


    def retrieve_lora_data_by_hash(self, root_dictionary=None, lora_hash: str="") -> tuple:
        """
        Retrieves LoRA model data by its hash from the root dictionary.

        Parameters:
            root_dictionary (dict, optional): The dictionary containing LoRA data. If None, the dictionary
                                            is loaded from the file specified by `self.model_dictionary_path`.
            lora_hash (str): The hash of the LoRA model to retrieve.

        Returns:
            tuple: A tuple containing the name key associated with the hash and the corresponding model data.
                If the hash or name key is missing, the model data includes an error message.
        """
        if root_dictionary is None:
            root_dictionary = self.load_json_file(self.model_dictionary_path)
        # if not FileHandler.validate_root_dictionary(root_dictionary):
        #     return "", {"error": "Invalid dictionary"}
        lora_key_name = root_dictionary["lora"]["hash"].get(lora_hash)
        if lora_key_name:
            model_data = root_dictionary["lora"]["name"].get(lora_key_name)
            if model_data:
                return lora_key_name, model_data
            return lora_key_name, {"error": "Missing lora_key_name in dictionary"}
        return lora_key_name, {"error": "Missing lora_hash in dictionary"}


    def retrieve_ckpt_data_by_name(self, root_dictionary=None, ckpt_key_name: str="") -> tuple:
        """
        Retrieves checkpoint model data by its name key from the root dictionary.

        Parameters:
            root_dictionary (dict, optional): The dictionary containing checkpoint data. If None, the dictionary
                                            is loaded from the file specified by `self.model_dictionary_path`.
            ckpt_key_name (str): The name key of the checkpoint model to retrieve.

        Returns:
            tuple: A tuple containing the name key and the corresponding model data.
                If the name key is missing, the model data includes an error message.
        """
        if root_dictionary is None:
            root_dictionary = self.load_json_file(self.model_dictionary_path)
        # if not FileHandler.validate_root_dictionary(root_dictionary):
        #     return {"error": "Invalid dictionary"}
        model_data = root_dictionary["ckpt"]["name"].get(ckpt_key_name, {"error": "Missing ckpt_key_name in dictionary"})
        return ckpt_key_name, model_data


    def retrieve_ckpt_data_by_hash(self, root_dictionary=None, ckpt_hash: str="") -> tuple:
        """
        Retrieves checkpoint model data by its hash from the root dictionary.

        Parameters:
            root_dictionary (dict, optional): The dictionary containing checkpoint data. If None, the dictionary
                                            is loaded from the file specified by `self.model_dictionary_path`.
            ckpt_hash (str): The hash of the checkpoint model to retrieve.

        Returns:
            tuple: A tuple containing the name key associated with the hash and the corresponding model data.
                If the hash or name key is missing, the model data includes an error message.
        """
        if root_dictionary is None:
            root_dictionary = self.load_json_file(self.model_dictionary_path)
        # if not FileHandler.validate_root_dictionary(root_dictionary):
        #     return "", {"error": "Invalid dictionary"}
        ckpt_key_name = root_dictionary["ckpt"]["hash"].get(ckpt_hash)
        if ckpt_key_name:
            model_data = root_dictionary["ckpt"]["name"].get(ckpt_key_name)
            if model_data:
                return ckpt_key_name, model_data
            return ckpt_key_name, {"error": "Missing ckpt_key_name in dictionary"}
        return ckpt_key_name, {"error": "Missing ckpt_hash in dictionary"}


    def add_lora_entry(self, lora_entries: list):
        """
        Adds LoRA entries to the JSON dictionary file.

        Parameters:
            lora_entries (list): A list of dictionaries representing LoRA entries to be added.

            example_entries = [
                    {"example_lora": {"POSITIVE": "", ... "HASH": "","FILEPATH":""}},
                ]
        """
        self._add_to_json_dictionary(entries=lora_entries, entry_type="lora")


    def add_ckpt_entry(self, ckpt_entries: list):
        """
        Adds checkpoint entries to the JSON dictionary file.

        Parameters:
            ckpt_entries (list): A list of dictionaries representing checkpoint entries to be added.

            example_entries = [
                    {"example_ckpt": {"SAMPLER_NAME": "", ... "HASH":"","FILEPATH":""}}
                ]

        """
        self._add_to_json_dictionary(entries=ckpt_entries, entry_type="ckpt")


    def _add_to_json_dictionary(self, filepath: str=None, entries: list=None, entry_type: str="lora", relative_path: bool=True) -> dict:
        """
        Add entries to Dictionary in JSON file, preserve custom formatting, and save to file. Returns updated dictionary.

        Parameters:
            filepath: The path to the root dictionary.
            entries: A list of entries to be added to the appropriate parent dictionary (lora|ckpt)
                e.g.:
                    subdicts = [
                        {"lora_name_key": {"POSITIVE": "", ... "HASH": "1111111111", "FILEPATH": ""}},
                    ]
            entry_type: Either "lora" or "ckpt".
            relative_path: Whether the filepath parameter should be treated as relative to the calling script file or absolute.

        Return:
            Updated dictionary
        """
        if filepath is None:
            filepath = self.model_dictionary_path
        root_dict: dict = self.load_json_file(filepath, default={}, relative_path=relative_path)
        if not root_dict:
            raise FileNotFoundError(f"No JSON file found at '{filepath}'")
        type_dictionary: dict = root_dict.get(entry_type, {})
        if not type_dictionary:
            raise FileNotFoundError(f"No type dictionary '{entry_type}' in JSON file found at '{filepath}'")
        name_dictionary: dict = type_dictionary.get("name", {})
        hash_dictionary: dict = type_dictionary.get("hash", {})
        for entry in entries:
            for name_key, metadata in entry.items():
                name_dictionary[name_key] = metadata
                entry_hash = name_dictionary[name_key].get("HASH", "0")
                hash_dictionary[entry_hash] = name_key
        sorted_name_dict = dict(sorted(name_dictionary.items()))
        sorted_hash_dict = dict(sorted(hash_dictionary.items(), key=lambda x: int(x[0])))
        type_dictionary["name"] = sorted_name_dict
        type_dictionary["hash"] = sorted_hash_dict
        out_str = self.custom_format_dictionary(root_dict)
        self.save_json_file(filepath, out_str, relative_path=relative_path, preserve_string=True)
        return root_dict


    def populate_all_hashes(self, root_dictionary=None):
        """
        Populates the hash sub-dictionaries for both LoRA and checkpoint data in the root dictionary.

        Parameters:
            root_dictionary (dict, optional): The dictionary to populate. If None, the dictionary
                                                is loaded from the file specified by `self.model_dictionary_path`.

        Returns:
            None: Updates the root dictionary in place and saves it back to the file.
        """
        if root_dictionary is None:
            root_dictionary = self.load_json_file(self.model_dictionary_path)
        if not self.validate_root_dictionary(root_dictionary):
            logger.error("populate_all_hashes: Invalid dictionary")
            return
        self._populate_hash_subdict(root_dictionary["lora"])
        self._populate_hash_subdict(root_dictionary["ckpt"])
        self.custom_format_dictionary(root_dictionary)
        self.save_json_file(self.model_dictionary_path, root_dictionary)


    def _populate_hash_subdict(self, type_dictionary: dict):
        """
        Populates the 'hash' sub-dictionary in lora using the 'HASH' values
        from the 'name' sub-dictionary.

        :param lora: Dictionary containing 'name' and 'hash' sub-dictionaries.
        :return: None, modifies lora in place.
        """
        if "hash" not in type_dictionary:
            type_dictionary["hash"] = {}
        for name_key, metadata in type_dictionary.get("name", {}).items():
            if "HASH" in metadata and metadata["HASH"] != "":
                hash_value = metadata["HASH"]
                type_dictionary["hash"][hash_value] = name_key
        type_dictionary["hash"] = dict(sorted(type_dictionary["hash"].items(), key=lambda x: int(x[0])))


    @staticmethod
    def log_dicts(lora_dict, ckpt_dict=None) -> None:
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
        if not os.path.exists(source_path):
            raise ValueError(f"File not found: {source_path}")
        if source_path == destination_path:
            logger.debug("Cancel move: %s = %s", source_path, destination_path)
            return
        dest_is_dir = os.path.isdir(destination_path)
        dest_exists = os.path.exists(destination_path)
        if dest_exists:
            if dest_is_dir:
                target_path = os.path.join(destination_path, os.path.basename(source_path))
            else:
                logging.debug("Move failed! Destination file already exists: %s", destination_path)
                return False
        else:
            parent_dir = os.path.dirname(destination_path) or '.'
            os.makedirs(parent_dir, exist_ok=True)
            target_path = destination_path
        if os.path.exists(target_path):
            logging.debug(f"Move failed! Target path already exists: {target_path}")
            return False
        try:
            shutil.move(source_path, target_path)
            if not quiet:
                logging.debug("Successfully moved %s to %s", source_path, target_path)
            return True
        except Exception as e:
            logging.exception("Error moving file: %s", e, exc_info=1,  stack_info=True)
            return False


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


    @staticmethod
    def custom_format_dictionary(root_dictionary: dict) -> str:
        """
        Format a dictionary to a string with the desired structure:
        - Outer dictionaries are spaced with indents.
        - Inner leaf dictionaries remain on a single line.

        Parameters:
        root_dictionary: The dictionary to be formatted.

        Return:
            '{
                "lora": {
                    "name": {
                        "Default_LoRA": {"POSITIVE": "", ... "HASH": "1111111111", "FILEPATH": ""}
                    },
                    "hash": {
                        "1111111111": "Default_LoRA"
                    }
                },
                "ckpt": {
                    "name": {
                        "Default_Ckpt": {"SAMPLER_NAME": "euler_ancestral", ... "HASH": "2222222222", "FILEPATH": ""}
                    },
                    "hash": {
                        "2222222222": "Default_Ckpt"
                    }
                }
            }'
        """
        result = []
        for sub_key in root_dictionary.keys():
            sub_dict = root_dictionary[sub_key]
            max_key_length = max((key for key in map(len, sub_dict["name"].keys())), default = 0)
            formatted_name_entries = []
            for key, value in sub_dict["name"].items():
                entry_str = f'            "{key}": {" " * (max_key_length - len(key))}{json.dumps(value, separators=(", ", ": "))}'
                formatted_name_entries.append(entry_str)
            formatted_name = ",\n".join(formatted_name_entries)
            formatted_hash = json.dumps(sub_dict["hash"], indent=4, separators=(", ", ": ")).replace("\n", "\n        ")
            sub_dict_result = (
                f'\n'
                f'    "{sub_key}": {{\n'
                '        "name": {\n'
                f'{formatted_name}\n'
                '        },\n'
                '        "hash": '
                f'{formatted_hash}\n'
                '    }'
            )
            result.append(sub_dict_result)
        return "{" + ",\n\n\n".join(result) + "\n}"
