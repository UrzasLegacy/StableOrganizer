import json

# Import the functions to test
from pytest_mock.plugin import MockerFixture
from handlers.FileHandler import FileHandler
from handlers.ModelDictHandler import (
    ModelDictHandler,
)

# fmt: off
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
# fmt: on


# Mock the model_dict_handler instance
config_data = {"model_dict_path": "tests/mock_AliDictionaries.json"}
file_handler = FileHandler(config_data)


# Test for _populate_hash_subdict
def test_populate_hash_subdict(mocker):
    type_dictionary = {
        "name": {
            "item1": {"HASH": "2", "other": "data1"},
            "item2": {"HASH": "1", "other": "data2"},
            "item3": {"HASH": "", "other": "data3"},
            "item4": {"HASH": "10", "other": "data4"},
        },
    }
    model_dict_handler_class = ModelDictHandler
    mocker.patch.object(model_dict_handler_class, "_validate_model_dictionary", return_value=True)
    model_dict_handler = model_dict_handler_class(file_handler)
    model_dict_handler._populate_hash_subdict(type_dictionary)

    expected_hash = {
        "1": "item2",
        "2": "item1",
        "10": "item4",
    }

    assert type_dictionary["hash"] == expected_hash


def test_retrieve_lora_by_name(mocker: MockerFixture):
    mock_model_dict = {
        "lora": {
            "name": {
                "LORA1": {"HASH": "123", "other": "data1"},
                "LORA2": {"HASH": "456", "other": "data2"},
            },
            "hash": {
                "123": "LORA1",
                "456": "LORA2",
            },
        }
    }
    model_dict_handler_class = ModelDictHandler
    mocker.patch.object(model_dict_handler_class, "_validate_model_dictionary", return_value=True)
    model_dict_handler = model_dict_handler_class(file_handler)
    mocker.patch.object(model_dict_handler, "model_dict", mock_model_dict)
    result = model_dict_handler.retrieve_lora_definition_by_name("LORA1")
    assert result == ("LORA1", {"HASH": "123", "other": "data1"})


def test_retrieve_lora_by_hash(mocker):
    mock_model_dict = {
        "lora": {
            "name": {
                "LORA1": {"HASH": "123", "other": "data1"},
                "LORA2": {"HASH": "456", "other": "data2"},
            },
            "hash": {
                "123": "LORA1",
                "456": "LORA2",
            },
        }
    }
    model_dict_handler_class = ModelDictHandler
    mocker.patch.object(model_dict_handler_class, "_validate_model_dictionary", return_value=True)
    model_dict_handler = model_dict_handler_class(file_handler)
    mocker.patch.object(model_dict_handler, "model_dict", mock_model_dict)
    result = model_dict_handler.retrieve_lora_definition_by_hash("456")
    assert result == ("LORA2", {"HASH": "456", "other": "data2"})


def test_retrieve_ckpt_by_name(mocker):
    mock_model_dict = {
        "ckpt": {
            "name": {
                "CKPT1": {"HASH": "789", "other": "data3"},
                "CKPT2": {"HASH": "101112", "other": "data4"},
            },
            "hash": {
                "789": "CKPT1",
                "101112": "CKPT2",
            },
        }
    }
    model_dict_handler_class = ModelDictHandler
    mocker.patch.object(model_dict_handler_class, "_validate_model_dictionary", return_value=True)
    model_dict_handler = model_dict_handler_class(file_handler)
    mocker.patch.object(model_dict_handler, "model_dict", mock_model_dict)
    result = model_dict_handler.retrieve_ckpt_definition_by_name("CKPT2")
    assert result == ("CKPT2", {"HASH": "101112", "other": "data4"})


def test_retrieve_ckpt_by_hash(mocker):
    mock_model_dict = {
        "ckpt": {
            "name": {
                "CKPT1": {"HASH": "789", "other": "data3"},
                "CKPT2": {"HASH": "101112", "other": "data4"},
            },
            "hash": {
                "789": "CKPT1",
                "101112": "CKPT2",
            },
        }
    }
    model_dict_handler_class = ModelDictHandler
    mocker.patch.object(model_dict_handler_class, "_validate_model_dictionary", return_value=True)
    model_dict_handler = model_dict_handler_class(file_handler)
    mocker.patch.object(model_dict_handler, "model_dict", mock_model_dict)
    result = model_dict_handler.retrieve_ckpt_definition_by_hash("789")
    assert result == ("CKPT1", {"HASH": "789", "other": "data3"})


# Test for save_json_file (using tmp_path fixture for file system isolation)
def test_save_json_file(mocker, tmp_path):
    file_handler = FileHandler(config_data)
    model_dict_handler_class = ModelDictHandler
    mocker.patch.object(model_dict_handler_class, "_validate_model_dictionary", return_value=True)
    model_dict_handler = model_dict_handler_class(file_handler)
    test_file = tmp_path / "test.json"
    mock_data = {"lora": {"name": {"key": "value"}, "hash": {}}}
    mocker.patch.object(model_dict_handler, "model_dict", mock_data)
    mocker.patch.object(file_handler, "model_dict_path", test_file)

    model_dict_handler._save_model_dict()
    assert test_file.exists()
    with open(test_file, "r", encoding="UTF-8") as f:
        content = json.load(f)
    assert content == mock_data
