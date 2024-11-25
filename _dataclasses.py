from dataclasses import dataclass, asdict, field
from typing import Optional, List


# region UnifiedDict
@dataclass
class DuplicateInfo:
    category: str
    quality: str
    has_model: bool
    has_png: bool

    def to_dict(self):
        return asdict(self)


@dataclass
class LoraEntry:
    model_path: Optional[str]
    png_path: Optional[str]
    duplicates: List[DuplicateInfo] = field(default_factory=list)

    def to_dict(self):
        return {
            "model_path": self.model_path,
            "png_path": self.png_path,
            "duplicates": [dup.to_dict() for dup in self.duplicates],
        }


# region ModelDictionaries.json
@dataclass
class LoraDefinition:
    POSITIVE: Optional[str] = ""
    NEGATIVE: Optional[str] = ""
    NULLIFIERS: Optional[str] = ""
    WEIGHT: Optional[str] = "1.0"
    ASPECT_RATIO: Optional[str] = ""
    NOTES: Optional[str] = ""
    HASH: Optional[str] = "0"
    FILEPATH: Optional[str] = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class CkptDefinition:
    SAMPLER_NAME: Optional[str] = "euler_ancestral"
    SCHEDULER_NAME: Optional[str] = "normal"
    STEPS: Optional[int] = 30
    CFG: Optional[int] = 7
    VAE_NAME: Optional[str] = "sdxl_vae"
    POSITIVE: Optional[str] = "score_9, score_8_up, score_7_up"
    NEGATIVE: Optional[str] = ""
    NULLIFIER: Optional[str] = ""
    ASPECT_RATIO: Optional[str] = ""
    NOTES: Optional[str] = "DEFAULT SETTINGS"
    HASH: Optional[str] = "0"
    FILEPATH: Optional[str] = ""

    def to_dict(self):
        return asdict(self)
