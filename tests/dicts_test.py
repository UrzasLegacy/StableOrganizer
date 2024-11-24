import logging
import pytest
from handlers import InfoHandler
import os
import json

ROOT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

log_file_path = os.path.join(ROOT_DIRECTORY, "debugging.log")
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)


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


def test_matching_lora_and_png_in_different_qualities(mocker):
    """Test that LoRA and PNG with the same name in different qualities are merged correctly."""
    lora_dict = {
        "Attire": {
            "Difficult": {
                "ExampleLora": "C:\\LoraModels\\Attire_Difficult\\ExampleLora.safetensors"
            }
        }
    }
    png_dict = {
        "Attire": {
            "Scoring": {
                "ExampleLora": "C:\\LoraCards\\Attire_Scoring\\ExampleLora_TestCards"
            }
        }
    }
    expected_output = {
        "Attire": {
            "Scoring": {
                "ExampleLora": (
                    "C:\\LoraModels\\Attire_Difficult\\ExampleLora.safetensors",
                    "C:\\LoraCards\\Attire_Scoring\\ExampleLora_TestCards"
                )
            }
        }
    }

    mocker.patch('handlers.InfoHandler.InfoHandler.build_lora_dictionary', return_value=lora_dict)
    mocker.patch('handlers.InfoHandler.InfoHandler.build_png_dictionary', return_value=png_dict)
    mocker.patch('handlers.InfoHandler.InfoHandler.initialize_dictionary_template', return_value={})

    instance = InfoHandler({})
    result = instance.get_unified_lora_dictionary()

    assert result == expected_output


def test_lora_first_in_png_then_in_lora(mocker):
    """Test that a LoRA name first seen in png_dict is correctly merged when found in lora_dict."""
    lora_dict = {
        "Attire": {
            "Difficult": {
                "Bike_Shorts_Attire": "C:\\LoraModels\\Attire_Difficult\\Bike_Shorts_Attire.safetensors"
            }
        }
    }
    png_dict = {
        "Attire": {
            "Scoring": {
                "Bike_Shorts_Attire": "C:\\LoraCards\\Attire_Scoring\\Bike_Shorts_Attire_TestCards"
            }
        }
    }
    expected_output = {
        "Attire": {
            "Scoring": {
                "Bike_Shorts_Attire": (
                    "C:\\LoraModels\\Attire_Difficult\\Bike_Shorts_Attire.safetensors",
                    "C:\\LoraCards\\Attire_Scoring\\Bike_Shorts_Attire_TestCards"
                )
            }
        }
    }

    mocker.patch('handlers.InfoHandler.InfoHandler.build_lora_dictionary', return_value=lora_dict)
    mocker.patch('handlers.InfoHandler.InfoHandler.build_png_dictionary', return_value=png_dict)
    mocker.patch('handlers.InfoHandler.InfoHandler.initialize_dictionary_template', return_value={})

    instance = InfoHandler({})
    result = instance.get_unified_lora_dictionary()

    assert result == expected_output


def test_lora_first_in_lora_then_in_png(mocker):
    """Test that a LoRA name first seen in lora_dict is correctly merged when found in png_dict."""
    lora_dict = {
        "Attire": {
            "Difficult": {
                "T_Shirt_Attire": "C:\\LoraModels\\Attire_Difficult\\T_Shirt_Attire.safetensors"
            }
        }
    }
    png_dict = {
        "Attire": {
            "Scoring": {
                "T_Shirt_Attire": "C:\\LoraCards\\Attire_Scoring\\T_Shirt_Attire_TestCards"
            }
        }
    }
    expected_output = {
        "Attire": {
            "Scoring": {
                "T_Shirt_Attire": (
                    "C:\\LoraModels\\Attire_Difficult\\T_Shirt_Attire.safetensors",
                    "C:\\LoraCards\\Attire_Scoring\\T_Shirt_Attire_TestCards"
                )
            }
        }
    }

    mocker.patch('handlers.InfoHandler.InfoHandler.build_lora_dictionary', return_value=lora_dict)
    mocker.patch('handlers.InfoHandler.InfoHandler.build_png_dictionary', return_value=png_dict)
    mocker.patch('handlers.InfoHandler.InfoHandler.initialize_dictionary_template', return_value={})

    instance = InfoHandler({})
    result = instance.get_unified_lora_dictionary()

    assert result == expected_output


def test_lora_and_png_in_same_quality(mocker):
    """Test that LoRA and PNG with the same name in the same quality are merged correctly."""
    lora_dict = {
        "Attire": {
            "Scoring": {
                "Hat_Attire": "C:\\LoraModels\\Attire_Scoring\\Hat_Attire.safetensors"
            }
        }
    }
    png_dict = {
        "Attire": {
            "Scoring": {
                "Hat_Attire": "C:\\LoraCards\\Attire_Scoring\\Hat_Attire_TestCards"
            }
        }
    }
    expected_output = {
        "Attire": {
            "Scoring": {
                "Hat_Attire": (
                    "C:\\LoraModels\\Attire_Scoring\\Hat_Attire.safetensors",
                    "C:\\LoraCards\\Attire_Scoring\\Hat_Attire_TestCards"
                )
            }
        }
    }

    mocker.patch('handlers.InfoHandler.InfoHandler.build_lora_dictionary', return_value=lora_dict)
    mocker.patch('handlers.InfoHandler.InfoHandler.build_png_dictionary', return_value=png_dict)
    mocker.patch('handlers.InfoHandler.InfoHandler.initialize_dictionary_template', return_value={})

    instance = InfoHandler({})
    result = instance.get_unified_lora_dictionary()

    assert result == expected_output


def test_lora_name_in_multiple_qualities(mocker):
    """Test that a LoRA name appearing in multiple qualities is merged correctly and duplicates are tracked."""
    lora_dict = {
        "Attire": {
            "Difficult": {
                "Gloves_Attire": "C:\\LoraModels\\Attire_Difficult\\Gloves_Attire.safetensors"
            },
            "Scoring": {
                "Gloves_Attire": "C:\\LoraModels\\Attire_Scoring\\Gloves_Attire.safetensors"
            }
        }
    }
    png_dict = {
        "Attire": {
            "Scoring": {
                "Gloves_Attire": "C:\\LoraCards\\Attire_Scoring\\Gloves_Attire_TestCards"
            }
        }
    }
    expected_output = {
        "Attire": {
            "Scoring": {
                "Gloves_Attire": [
                    "C:\\LoraModels\\Attire_Scoring\\Gloves_Attire.safetensors",
                    "C:\\LoraCards\\Attire_Scoring\\Gloves_Attire_TestCards",
                    []
                ]
            },
            "Difficult": {
                "Gloves_Attire": [
                    "C:\\LoraModels\\Attire_Difficult\\Gloves_Attire.safetensors",
                    None,
                    [["Attire", "Scoring"]]
                ]
            }
        }
    }

    mocker.patch('handlers.InfoHandler.InfoHandler.build_lora_dictionary', return_value=lora_dict)
    mocker.patch('handlers.InfoHandler.InfoHandler.build_png_dictionary', return_value=png_dict)
    mocker.patch('handlers.InfoHandler.InfoHandler.initialize_dictionary_template', return_value={})

    instance = InfoHandler({})
    result = instance.get_unified_lora_dictionary()
    logging.debug(f"DEBUG+++++++{json.dumps(result,indent=2)}")

    # Access the duplicates from the function if it returns them
    # For this example, let's assume we adjust the function to return duplicates
    # as a second value (result, duplicates)
    # So modify your function to return result, duplicates
    # For now, we'll mock this behavior
    duplicates = {
        "Gloves_Attire": [("Attire", "Difficult"), ("Attire", "Scoring")]
    }

    assert result == expected_output



def test_png_without_lora_gets_merged_when_lora_is_found(mocker):
    """Test that a PNG without a LoRA file gets merged correctly when the LoRA file is found later."""
    lora_dict = {
        "Attire": {
            "Difficult": {
                "Scarf_Attire": "C:\\LoraModels\\Attire_Difficult\\Scarf_Attire.safetensors"
            }
        }
    }
    png_dict = {
        "Attire": {
            "Scoring": {
                "Scarf_Attire": "C:\\LoraCards\\Attire_Scoring\\Scarf_Attire_TestCards"
            },
            "Good": {
                "Scarf_Attire": "C:\\LoraCards\\Attire_Good\\Scarf_Attire_TestCards"
            }
        }
    }
    expected_output = {
        "Attire": {
            "Difficult": {
                "Scarf_Attire": (
                    "C:\\LoraModels\\Attire_Difficult\\Scarf_Attire.safetensors",
                    "C:\\LoraCards\\Attire_Scoring\\Scarf_Attire_TestCards"
                )
            }
        }
    }

    mocker.patch('handlers.InfoHandler.InfoHandler.build_lora_dictionary', return_value=lora_dict)
    mocker.patch('handlers.InfoHandler.InfoHandler.build_png_dictionary', return_value=png_dict)
    mocker.patch('handlers.InfoHandler.InfoHandler.initialize_dictionary_template', return_value={})

    instance = InfoHandler({})
    result = instance.get_unified_lora_dictionary()

    assert result == expected_output
