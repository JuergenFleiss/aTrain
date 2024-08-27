import os

import yaml
from aTrain_core.globals import ATRAIN_DIR, DOCUMENTS_DIR
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


def check_access(path: str) -> bool:
    """Check if the application has access to the given path."""
    try:
        # Check if the directory exists and is readable
        if os.path.isdir(path):
            return len(os.listdir(path)) >= 0
        else:
            with open(path, "r") as f:
                f.read()
        return True
    except PermissionError:
        return False
    except FileNotFoundError:
        return False


def show_permission_instructions():
    """Show a message box with instructions for granting permissions."""
    print(
        "Access Required",
        "This application needs access to the Documents folder. Please grant this access in System Preferences > Security & Privacy > Privacy > Files and Folders.",
    )
