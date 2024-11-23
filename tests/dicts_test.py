import pytest
from handlers import InfoHandler

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

    # Mock the methods to return mock data.
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
