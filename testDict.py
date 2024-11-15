from handlers import FileHandler
import os
ROOT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ALI_DICT = {
    "lora": {
        "name": {
            "DEFAULT_LORA": {"POSITIVE": "", "WEIGHT": "1.0", "NEGATIVE": "", "NULLIFIERS": "","NOTES":"","HASH": "0","FILEPATH":""},
        },
        "hash": {
            "0": "DEFAULT_LORA"
        }
    },
    "ckpt": {
        "name": {
            "DEFAULT_CKPT": {"SAMPLER_NAME": "euler_ancestral", "SCHEDULER_NAME": "normal", "STEPS": 30, "CFG": 7, "VAE_NAME": "sdxl_vae", "POSITIVE": "score_9, score_8_up, score_7_up", "NEGATIVE": "", "NULLIFIER": "", "ASPECT_RATIO":"", "NOTES":"DEFAULT SETTINGS", "HASH": "0", "FILEPATH": ""},
        },
        "hash": {
            "0": "DEFAULT_CKPT"
        }
    }
}


def _populate_hash_subdict(type_dictionary: dict):
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

def load_config() -> dict:
    if os.path.exists(config_path):
        config = FileHandler.load_json_file(config_path, default={}, relative_path=False)
        return config

import json

dict_path = os.path.join(ROOT_DIRECTORY, "AliDictionaries.json")
config_path = os.path.join(ROOT_DIRECTORY, "config.json")
config_data = load_config()
file_handler = FileHandler(config_data)
root_dictionary = file_handler.load_json_file(dict_path, default=DEFAULT_ALI_DICT, relative_path=True)
log_file_path = os.path.splitext(os.path.abspath(__file__))[0] + "_dict.log"
lora_entries = [
    {"NEW_LORA2": {"POSITIVE": "", "WEIGHT": "1.0", "NEGATIVE": "", "NULLIFIERS": "","NOTES":"","HASH": "1","FILEPATH":""}},
    {"NEW_LORA3": {"POSITIVE": "", "WEIGHT": "1.0", "NEGATIVE": "", "NULLIFIERS": "","NOTES":"","HASH": "2","FILEPATH":""}},
    {"NEW_LORA4": {"POSITIVE": "", "WEIGHT": "1.0", "NEGATIVE": "", "NULLIFIERS": "","NOTES":"","HASH": "3","FILEPATH":""}},
    {"NEW_LORA5": {"POSITIVE": "", "WEIGHT": "1.0", "NEGATIVE": "", "NULLIFIERS": "","NOTES":"","HASH": "4","FILEPATH":""}},
    {"NEW_LORA6": {"POSITIVE": "", "WEIGHT": "1.0", "NEGATIVE": "", "NULLIFIERS": "","NOTES":"","HASH": "5","FILEPATH":""}},
    {"NEW_LORA7": {"POSITIVE": "", "WEIGHT": "1.0", "NEGATIVE": "", "NULLIFIERS": "","NOTES":"","HASH": "624124","FILEPATH":""}}
]
ckpt_entries = [
    {"DEFAULT": {"SAMPLER_NAME": "euler_ancestral", "SCHEDULER_NAME": "normal", "STEPS": 30, "CFG": 7, "VAE_NAME": "sdxl_vae", "POSITIVE": "score_9, score_8_up, score_7_up", "NEGATIVE": "", "NULLIFIER": "", "ASPECT_RATIO": "", "NOTES": "THESE ARE DEFAULT SETTINGS, NO ENTRY IN DICTIONARY FOR THIS MODEL", "HASH": "6"}}

]


def save_json_file(file: str, data: dict|str, relative_path: bool=True, preserve_string: bool=False):
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



def add_lora_entry(lora_entries):
    file_handler._add_to_json_dictionary(entries=lora_entries, entry_type="lora")

def add_ckpt_entry(ckpt_entries):
    file_handler._add_to_json_dictionary(entries=ckpt_entries, entry_type="ckpt")

def populate_all_hashes():
    _populate_hash_subdict(root_dictionary["lora"])
    _populate_hash_subdict(root_dictionary["ckpt"])
    with open(log_file_path,"w") as f:
        f.write(file_handler.custom_format_dictionary(root_dictionary))

def retrieve_lora_by_name(name):
    return file_handler.retrieve_lora_data_by_name(root_dictionary,name)

def retrieve_lora_by_hash(hash):
    return file_handler.retrieve_lora_data_by_hash(root_dictionary,hash)

def retrieve_ckpt_by_name(name):
    return file_handler.retrieve_ckpt_data_by_name(root_dictionary,name)

def retrieve_ckpt_by_hash(hash):
    return file_handler.retrieve_ckpt_data_by_hash(root_dictionary,hash)
#add_lora_entry(lora_entries)
#add_ckpt_entry(ckpt_entries)
# populate_all_hashes()
t =file_handler.retrieve_lora_data_by_hash(root_dictionary, "624124")
print(t)
# test_retrieve_by_name("Nakatsu22_Style")