from enum import Enum


DEFAULT_CONFIG = {
  "ckpt_processing_dir": None,
  "lora_processing_dir": None,
  "ckpt_png_dir": None,
  "lora_png_dir": None,
  "ckpt_model_dir": None,
  "lora_model_dir": None,
  "output_dir": None
}


class TreeNodeTag(Enum):
    HAS_IMAGES = "has_imgs"
    NO_IMAGES = "no_imgs"
    DIR_MISMATCH = "dir_mismatch"
    NO_MODEL = "no_model"

class ConfigKey(Enum):
    CKPT_PROCESSING_DIR = "ckpt_processing_dir"
    LORA_PROCESSING_DIR = "lora_processing_dir"
    CKPT_PNG_DIR = "ckpt_png_dir"
    LORA_PNG_DIR = "lora_png_dir"
    CKPT_MODEL_DIR = "ckpt_model_dir"
    LORA_MODEL_DIR = "lora_model_dir"
    OUTPUT_DIR = "output_dir"


print(TreeNodeTag.HAS_IMAGES.value)
