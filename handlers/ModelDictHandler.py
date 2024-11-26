"""Utilities for the ModelDictionaries.json"""

import json
import logging

# from _dataclasses import CkptDefinition, LoraDefinition
from handlers.Interfaces import DataStoreInterface

# fmt: off
DEFAULT_MODEL_DICT = {
    "lora": {
        "name": {
            "DEFAULT_LORA": {"POSITIVE": "", "WEIGHT": "1.0", "NEGATIVE": "", "NULLIFIERS": "", "NOTES": "", "HASH": "0", "FILEPATH": ""},
        },
        "hash": {
            "0": "DEFAULT_LORA"
        },
    },
    "ckpt": {
        "name": {
            "DEFAULT_CKPT": { "SAMPLER_NAME": "euler_ancestral", "SCHEDULER_NAME": "normal", "STEPS": 30, "CFG": 7, "VAE_NAME": "sdxl_vae", "POSITIVE": "score_9, score_8_up, score_7_up", "NEGATIVE": "", "NULLIFIER": "", "ASPECT_RATIO": "", "NOTES": "DEFAULT SETTINGS", "HASH": "0", "FILEPATH": ""},
        },
        "hash": {
            "0": "DEFAULT_CKPT"
        },
    },
}
# fmt: on

logger = logging.getLogger(__file__)


class ModelDictHandler:
    def __init__(self, data_store: DataStoreInterface):
        self.data_store = data_store
        self._initialize_model_dict()

    @property
    def get_model_dict(self):
        return self.model_dict

    def _initialize_model_dict(self):
        self.model_dict = self.data_store.load_data()
        if not self._validate_model_dictionary():
            logger.exception("Can't initialize invalid root dictionary.", exc_info=1, stack_info=True)
            raise ValueError("Can't initialize invalid root dictionary.")

    def _load_model_dict(self):
        return self.data_store.load_data()

    def _save_model_dict(self):
        out_str = self.custom_format_dictionary()
        return self.data_store.save_data(out_str)

    def _validate_model_dictionary(self) -> bool:
        """Validates the structure of the root model dictionary for required keys and types.

        Returns:
            bool: True if the root dictionary is valid, ValueError otherwise."""
        if not self.model_dict:
            raise ValueError(f"Root dictionary isn't initialized.\n{self.model_dict}")
        if not isinstance(self.model_dict, dict) or "lora" not in self.model_dict or "ckpt" not in self.model_dict:
            raise ValueError(f"Root dictionary is invalid.\n{self.model_dict}")
        lora_data = self.model_dict.get("lora", {})
        if not isinstance(lora_data, dict) or "hash" not in lora_data or "name" not in lora_data:
            raise ValueError(f"LoRA dictionary is invalid.\n{lora_data}")
        ckpt_data = self.model_dict.get("ckpt", {})
        if not isinstance(ckpt_data, dict) or "hash" not in ckpt_data or "name" not in ckpt_data:
            raise ValueError(f"Ckpt dictionary is invalid.\n{ckpt_data}")
        return True

    def retrieve_lora_definition_by_name(self, lora_key_name: str = "") -> tuple:
        """Retrieves LoRA model data by its name key from the root dictionary.

        Parameters:
            lora_key_name (str): The name key of the LoRA model to retrieve.

        Returns:
            tuple: A tuple containing the name key and the corresponding model data.
                If the name key is missing, the model data includes an error message."""
        self._validate_model_dictionary()
        model_data = self.model_dict["lora"]["name"].get(
            lora_key_name, {"error": "Missing lora_key_name in dictionary"}
        )
        return lora_key_name, model_data

    def retrieve_lora_definition_by_hash(self, lora_hash: str = "") -> tuple:
        """Retrieves LoRA model data by its hash from the root dictionary.

        Parameters:
            lora_hash (str): The hash of the LoRA model to retrieve.

        Returns:
            tuple: A tuple containing the name key associated with the hash and the corresponding model data.
                If the hash or name key is missing, the model data includes an error message.
        """
        self._validate_model_dictionary()
        lora_key_name = self.model_dict["lora"]["hash"].get(lora_hash)
        if lora_key_name:
            model_data = self.model_dict["lora"]["name"].get(lora_key_name)
            if model_data:
                return lora_key_name, model_data
            return lora_key_name, {"error": "Missing lora_key_name in dictionary"}
        return lora_key_name, {"error": "Missing lora_hash in dictionary"}

    def retrieve_ckpt_definition_by_name(self, ckpt_key_name: str = "") -> tuple:
        """Retrieves checkpoint model data by its name key from the root dictionary.

        Parameters:
            ckpt_key_name (str): The name key of the checkpoint model to retrieve.

        Returns:
            tuple: A tuple containing the name key and the corresponding model data.
                If the name key is missing, the model data includes an error message."""
        self._validate_model_dictionary()
        model_data = self.model_dict["ckpt"]["name"].get(
            ckpt_key_name, {"error": "Missing ckpt_key_name in dictionary"}
        )
        return ckpt_key_name, model_data

    def retrieve_ckpt_definition_by_hash(self, ckpt_hash: str = "") -> tuple:
        """Retrieves checkpoint model data by its hash from the root dictionary.

        Parameters:
            ckpt_hash (str): The hash of the checkpoint model to retrieve.

        Returns:
            tuple: A tuple containing the name key associated with the hash and the corresponding model data.
                If the hash or name key is missing, the model data includes an error message.
        """
        self._validate_model_dictionary()
        ckpt_key_name = self.model_dict["ckpt"]["hash"].get(ckpt_hash)
        if ckpt_key_name:
            model_data = self.model_dict["ckpt"]["name"].get(ckpt_key_name)
            if model_data:
                return ckpt_key_name, model_data
            return ckpt_key_name, {"error": "Missing ckpt_key_name in dictionary"}
        return ckpt_key_name, {"error": "Missing ckpt_hash in dictionary"}

    def add_lora_entry_to_model_dict(self, lora_entries: list):
        """Adds LoRA entries to the JSON dictionary file.

        Parameters:
            lora_entries (list): A list of dictionaries representing LoRA entries to be added.

            example_entries = [
                    {"example_lora": {"POSITIVE": "", ... "HASH": "","FILEPATH":""}},
                ]"""
        self._validate_model_dictionary()
        self._add_to_model_dict(entries=lora_entries, entry_type="lora")

    def add_ckpt_entry_to_model_dict(self, ckpt_entries: list):
        """Adds checkpoint entries to the JSON dictionary file.

        Parameters:
            ckpt_entries (list): A list of dictionaries representing checkpoint entries to be added.

            example_entries = [
                    {"example_ckpt": {"SAMPLER_NAME": "", ... "HASH":"","FILEPATH":""}}
                ]"""
        self._validate_model_dictionary()
        self._add_to_model_dict(entries=ckpt_entries, entry_type="ckpt")

    def _add_to_model_dict(self, entries: list = None, entry_type: str = "lora") -> dict:
        """Add entries to Dictionary in JSON file, preserve custom formatting, and save to file. Returns updated dictionary.

        Parameters:
            entries: A list of entries to be added to the appropriate parent dictionary (lora|ckpt)
                e.g.:
                    subdicts = [
                        {"lora_name_key": {"POSITIVE": "", ... "HASH": "1111111111", "FILEPATH": ""}},
                    ]
            entry_type: Either "lora" or "ckpt".

        Return:
            None, modifies self.model_dict in place"""
        self._validate_model_dictionary()
        type_dictionary: dict = self.model_dict.get(entry_type, {})
        if not type_dictionary:
            raise FileNotFoundError(f"No type dictionary '{entry_type}' in model dictionary.")
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
        self._save_model_dict()

    def populate_all_hashes(self):
        """Populates the hash sub-dictionaries for both LoRA and checkpoint data in the root dictionary.

        Parameters:
            self.model_dict (dict, optional): The dictionary to populate.

        Returns:
            None: Updates the root dictionary in place and saves it back to the file."""
        self._validate_model_dictionary()
        self._populate_hash_subdict(self.model_dict["lora"])
        self._populate_hash_subdict(self.model_dict["ckpt"])
        self._save_model_dict()

    def _populate_hash_subdict(self, type_dictionary: dict):
        """Populates the 'hash' sub-dictionary in lora using the 'HASH' values
        from the 'name' sub-dictionary.

        :param lora: Dictionary containing 'name' and 'hash' sub-dictionaries.
        :return: None, modifies lora in place."""
        if "hash" not in type_dictionary:
            type_dictionary["hash"] = {}
        for name_key, metadata in type_dictionary.get("name", {}).items():
            if "HASH" in metadata and metadata["HASH"] != "":
                hash_value = metadata["HASH"]
                type_dictionary["hash"][hash_value] = name_key
        type_dictionary["hash"] = dict(sorted(type_dictionary["hash"].items(), key=lambda x: int(x[0])))

    def custom_format_dictionary(self) -> str:
        """Format a dictionary to a string with the desired structure:
        - Outer dictionaries are spaced with indents.
        - Inner leaf dictionaries remain on a single line.

        Parameters:
        self.model_dict: The dictionary to be formatted.

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
        self._validate_model_dictionary()
        result = []
        for sub_key in self.model_dict.keys():
            sub_dict = self.model_dict[sub_key]
            max_key_length = max((key for key in map(len, sub_dict["name"].keys())), default=0)
            formatted_name_entries = []
            for key, value in sub_dict["name"].items():
                entry_str = f'            "{key}": {" " * (max_key_length - len(key))}{json.dumps(value, separators=(", ", ": "))}'
                formatted_name_entries.append(entry_str)
            formatted_name = ",\n".join(formatted_name_entries)
            formatted_hash = json.dumps(sub_dict["hash"], indent=4, separators=(", ", ": ")).replace("\n", "\n        ")
            sub_dict_result = (
                f"\n"
                f'    "{sub_key}": {{\n'
                '        "name": {\n'
                f"{formatted_name}\n"
                "        },\n"
                '        "hash": '
                f"{formatted_hash}\n"
                "    }"
            )
            result.append(sub_dict_result)
        return "{" + ",\n\n\n".join(result) + "\n}"
