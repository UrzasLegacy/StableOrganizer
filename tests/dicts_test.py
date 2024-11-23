import logging
import pytest
from handlers import InfoHandler
from handlers.CommandHandler import stack, TreeMoveCommand

logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def mock_data():
    lora_dict = {
        "Attire": {
            "In": {
                "Bike_Shorts_Attire": "C:\\LoraModels\\Attire_In\\Pony_XL_Bike_Shorts_Attire.safetensors"
            },
            "CloseAnalysis": {
                "T_Shirt_Attire": "C:\\LoraModels\\Attire_CloseAnalysis\\T_Shirt_Attire.safetensors"
            }
        }
    }
    png_dict = {
        "Attire": {
            "Scoring": {
                "Bike_Shorts_Attire": "C:\\LoraCards\\Attire_Scoring\\Bike_Shorts_Attire_TestCards"
            },
            "CloseAnalysis": {
                "T_Shirt_Attire": "C:\\LoraCards\\Attire_CloseAnalysis\\T_Shirt_Attire_TestCards"
            },
            "SFW": {
                "Hat_Attire": "C:\\LoraCards\\Attire_SFW\\Hat_Attire_TestCards"
            }
        }
    }
    expected_output = {
        "Attire": {
            "In": {
                "Bike_Shorts_Attire": (
                    "C:\\LoraModels\\Attire_In\\Pony_XL_Bike_Shorts_Attire.safetensors",
                    "C:\\LoraCards\\Attire_Scoring\\Bike_Shorts_Attire_TestCards"
                )
            },
            "CloseAnalysis": {
                "T_Shirt_Attire": (
                    "C:\\LoraModels\\Attire_CloseAnalysis\\T_Shirt_Attire.safetensors",
                    "C:\\LoraCards\\Attire_CloseAnalysis\\T_Shirt_Attire_TestCards"
                )
            },
            "SFW": {
                "Hat_Attire": (
                    None,
                    "C:\\LoraCards\\Attire_SFW\\Hat_Attire_TestCards"
                )
            }
        }
    }
    return lora_dict, png_dict, expected_output

def test_get_unified_lora_dictionary(mock_data, mocker):
    lora_dict, png_dict, expected_output = mock_data
    mocker.patch('handlers.InfoHandler.InfoHandler.build_lora_dictionary', return_value=lora_dict)
    mocker.patch('handlers.InfoHandler.InfoHandler.build_png_dictionary', return_value=png_dict)
    mocker.patch('handlers.InfoHandler.InfoHandler.initialize_dictionary_template', return_value={})
    instance = InfoHandler({})
    result = instance.get_unified_lora_dictionary()

    assert result == expected_output


def test_merge_logic_with_missing_entries(mocker):
    """Test if missing lora or png entries are handled correctly."""
    lora_dict = {
        "Attire": {
            "In": {
                "Pants_Attire": "C:\\LoraModels\\Attire_In\\Pants_Attire.safetensors"
            }
        }
    }
    png_dict = {
        "Attire": {
            "In": {
                "Hat_Attire": "C:\\LoraCards\\Attire_In\\Hat_Attire_TestCards"
            }
        }
    }
    expected_output = {
        "Attire": {
            "In": {
                "Pants_Attire": (
                    "C:\\LoraModels\\Attire_In\\Pants_Attire.safetensors",
                    None
                ),
                "Hat_Attire": (
                    None,
                    "C:\\LoraCards\\Attire_In\\Hat_Attire_TestCards"
                )
            }
        }
    }
    #lora_dict, png_dict, expected_output = map(InfoHandler.sort_built_dictionary, [lora_dict, png_dict, expected_output])

    mocker.patch('handlers.InfoHandler.InfoHandler.build_lora_dictionary', return_value=lora_dict)
    mocker.patch('handlers.InfoHandler.InfoHandler.build_png_dictionary', return_value=png_dict)
    mocker.patch('handlers.InfoHandler.InfoHandler.initialize_dictionary_template', return_value={})
    instance = InfoHandler({})
    result = instance.get_unified_lora_dictionary()
    assert result == expected_output

def test_empty_dictionaries(mocker):
    """Test with empty lora and png dictionaries."""
    lora_dict = {}
    png_dict = {}
    expected_output = {}

    mocker.patch('handlers.InfoHandler.InfoHandler.build_lora_dictionary', return_value=lora_dict)
    mocker.patch('handlers.InfoHandler.InfoHandler.build_png_dictionary', return_value=png_dict)
    mocker.patch('handlers.InfoHandler.InfoHandler.initialize_dictionary_template', return_value={})

    instance = InfoHandler({})

    result = instance.get_unified_lora_dictionary()

    assert result == expected_output


def test_merge_orphan_entries_dictionaries(mocker):
    unified_dict = {
        "Attire": {
            "In": {
                "Bodysuit_Attire": [
                    "C:\\AliProjects\\StableDiffusion\\StableOrganizerMock\\LoraModels\\Attire_In\\Pony_XL_Bodysuit_Attire.safetensors",
                    None
                ]
            },
            "SFW": {
                "Bike_Shorts_Attire": [
                    "C:\\AliProjects\\StableDiffusion\\StableOrganizerMock\\LoraModels\\Attire_SFW\\Pony_XL_Bike_Shorts_Attire.safetensors",
                    "C:\\AliProjects\\StableDiffusion\\StableOrganizerMock\\CardArchive\\LoraCards\\Attire_SFW\\FindForgetYou_v2_Bike_Shorts_Attire_TestCards"
                ]
            },
            "Good": {
                "Bodysuit_Attire": [
                    None,
                    "C:\\AliProjects\\StableDiffusion\\StableOrganizerMock\\CardArchive\\LoraCards\\Attire_Good\\FindForgetYou_v2_Bodysuit_Attire_TestCards"
                ]
            }
        },
        "Character": {},
        "Concept": {},
        "Style": {}
    }

    expected_output = {
        "Attire": {
            "In": {
                "Bodysuit_Attire": [
                    "C:\\AliProjects\\StableDiffusion\\StableOrganizerMock\\LoraModels\\Attire_In\\Pony_XL_Bodysuit_Attire.safetensors",
                    "C:\\AliProjects\\StableDiffusion\\StableOrganizerMock\\CardArchive\\LoraCards\\Attire_Good\\FindForgetYou_v2_Bodysuit_Attire_TestCards"
                ]
            },
            "SFW": {
                "Bike_Shorts_Attire": [
                    "C:\\AliProjects\\StableDiffusion\\StableOrganizerMock\\LoraModels\\Attire_SFW\\Pony_XL_Bike_Shorts_Attire.safetensors",
                    "C:\\AliProjects\\StableDiffusion\\StableOrganizerMock\\CardArchive\\LoraCards\\Attire_SFW\\FindForgetYou_v2_Bike_Shorts_Attire_TestCards"
                ]
            },
        },
        "Character": {},
        "Concept": {},
        "Style": {}
    }


    mocker.patch('handlers.InfoHandler.InfoHandler.initialize_dictionary_template', return_value={})

    instance = InfoHandler({})
    result = instance.reunify_lora_dictionary(unified_dict)

    assert result == expected_output