import os

import yaml
from aTrain_core.globals import ATRAIN_DIR
from pydantic import BaseModel, ValidationError

SETTINGS_FILE = os.path.join(ATRAIN_DIR, "settings.txt")


class Settings(BaseModel):
    """A type schema for the settings to be used in a transcription"""

    cuda_available: bool


def load_settings() -> Settings:
    """A function that loads the settings from a settings file and returns an instance of the Settings class."""
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as settings_file:
            settings_dict = yaml.safe_load(settings_file)
            settings = Settings(**settings_dict)
    except (ValidationError, FileNotFoundError, TypeError):
        settings = reset_settings()
    return settings


def reset_settings() -> Settings:
    """A function that resets the settings to defaults and checks for cuda availablity."""
    from torch import cuda

    cuda_available = cuda.is_available()
    settings = Settings(cuda_available=cuda_available)
    write_settings(settings)
    return settings


def write_settings(settings: Settings):
    """A function that saves the current settings to a settings file."""
    os.makedirs(ATRAIN_DIR, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as settings_file:
        yaml.safe_dump(settings.model_dump(), settings_file)
