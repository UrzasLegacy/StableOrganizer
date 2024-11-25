import pytest
import os
import json
from unittest.mock import MagicMock, patch

# Import the functions to test
from ModelDictHandler import (
    _populate_hash_subdict,
    save_json_file,
    retrieve_lora_by_name,
    retrieve_lora_by_hash,
    retrieve_ckpt_by_name,
    retrieve_ckpt_by_hash,
    DEFAULT_model_dict,
)

LORA_ENTRIES = [
    {"NEW_LORA2": {"POSITIVE": "", "WEIGHT": "1.0", "NEGATIVE": "", "NULLIFIERS": "","NOTES":"","HASH": "1","FILEPATH":""}},
    {"NEW_LORA3": {"POSITIVE": "", "WEIGHT": "1.0", "NEGATIVE": "", "NULLIFIERS": "","NOTES":"","HASH": "2","FILEPATH":""}},
    {"NEW_LORA4": {"POSITIVE": "", "WEIGHT": "1.0", "NEGATIVE": "", "NULLIFIERS": "","NOTES":"","HASH": "3","FILEPATH":""}},
    {"NEW_LORA5": {"POSITIVE": "", "WEIGHT": "1.0", "NEGATIVE": "", "NULLIFIERS": "","NOTES":"","HASH": "4","FILEPATH":""}},
    {"NEW_LORA6": {"POSITIVE": "", "WEIGHT": "1.0", "NEGATIVE": "", "NULLIFIERS": "","NOTES":"","HASH": "5","FILEPATH":""}},
    {"NEW_LORA7": {"POSITIVE": "", "WEIGHT": "1.0", "NEGATIVE": "", "NULLIFIERS": "","NOTES":"","HASH": "624124","FILEPATH":""}}
]
CKPT_ENTRIES = [
    {"DEFAULT": {"SAMPLER_NAME": "euler_ancestral", "SCHEDULER_NAME": "normal", "STEPS": 30, "CFG": 7, "VAE_NAME": "sdxl_vae", "POSITIVE": "score_9, score_8_up, score_7_up", "NEGATIVE": "", "NULLIFIER": "", "ASPECT_RATIO": "", "NOTES": "THESE ARE DEFAULT SETTINGS, NO ENTRY IN DICTIONARY FOR THIS MODEL", "HASH": "6"}}

]




# Since FileHandler is not provided, we'll create a mock for it
class MockFileHandler:
    def __init__(self, config_data):
        self.config_data = config_data

    def load_json_file(self, filepath, default={}, relative_path=False):
        # Simulate loading JSON data
        return default

    def retrieve_lora_definition_by_name(self, self.model_dict, name):
        return self.model_dict["lora"]["name"].get(name)

    def retrieve_lora_definition_by_hash(self, self.model_dict, hash_value):
        name = self.model_dict["lora"]["hash"].get(hash_value)
        if name:
            return self.model_dict["lora"]["name"].get(name)
        return None

    def retrieve_ckpt_definition_by_name(self, self.model_dict, name):
        return self.model_dict["ckpt"]["name"].get(name)

    def retrieve_ckpt_definition_by_hash(self, self.model_dict, hash_value):
        name = self.model_dict["ckpt"]["hash"].get(hash_value)
        if name:
            return self.model_dict["ckpt"]["name"].get(name)
        return None

# Mock the file_handler instance
config_data = {}
file_handler = MockFileHandler(config_data)

# Test for _populate_hash_subdict
def test_populate_hash_subdict():
    type_dictionary = {
        "name": {
            "item1": {"HASH": "2", "other": "data1"},
            "item2": {"HASH": "1", "other": "data2"},
            "item3": {"HASH": "", "other": "data3"},
            "item4": {"HASH": "10", "other": "data4"},
        },
    }

    _populate_hash_subdict(type_dictionary)

    expected_hash = {
        "1": "item2",
        "2": "item1",
        "10": "item4",
    }

    assert type_dictionary["hash"] == expected_hash

# Test for retrieve_lora_by_name
def test_retrieve_lora_by_name():
    self.model_dict = {
        "lora": {
            "name": {
                "LORA1": {"HASH": "123", "other": "data1"},
                "LORA2": {"HASH": "456", "other": "data2"},
            },
            "hash": {
                "123": "LORA1",
                "456": "LORA2",
            }
        }
    }
    result = file_handler.retrieve_lora_definition_by_name(self.model_dict, "LORA1")
    assert result == {"HASH": "123", "other": "data1"}

# Test for retrieve_lora_by_hash
def test_retrieve_lora_by_hash():
    self.model_dict = {
        "lora": {
            "name": {
                "LORA1": {"HASH": "123", "other": "data1"},
                "LORA2": {"HASH": "456", "other": "data2"},
            },
            "hash": {
                "123": "LORA1",
                "456": "LORA2",
            }
        }
    }
    result = file_handler.retrieve_lora_definition_by_hash(self.model_dict, "456")
    assert result == {"HASH": "456", "other": "data2"}

# Test for retrieve_ckpt_by_name
def test_retrieve_ckpt_by_name():
    self.model_dict = {
        "ckpt": {
            "name": {
                "CKPT1": {"HASH": "789", "other": "data3"},
                "CKPT2": {"HASH": "101112", "other": "data4"},
            },
            "hash": {
                "789": "CKPT1",
                "101112": "CKPT2",
            }
        }
    }
    result = file_handler.retrieve_ckpt_definition_by_name(self.model_dict, "CKPT2")
    assert result == {"HASH": "101112", "other": "data4"}

# Test for retrieve_ckpt_by_hash
def test_retrieve_ckpt_by_hash():
    self.model_dict = {
        "ckpt": {
            "name": {
                "CKPT1": {"HASH": "789", "other": "data3"},
                "CKPT2": {"HASH": "101112", "other": "data4"},
            },
            "hash": {
                "789": "CKPT1",
                "101112": "CKPT2",
            }
        }
    }
    result = file_handler.retrieve_ckpt_definition_by_hash(self.model_dict, "789")
    assert result == {"HASH": "789", "other": "data3"}

# Test for save_json_file (using tmp_path fixture for file system isolation)
def test_save_json_file(tmp_path):
    test_file = tmp_path / "test.json"
    data = {"key": "value"}
    save_json_file(str(test_file), data, relative_path=False)
    assert test_file.exists()
    with open(test_file, 'r', encoding='UTF-8') as f:
        content = json.load(f)
    assert content == data

