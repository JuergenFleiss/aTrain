from aTrain_core.globals import ATRAIN_DIR
import os
import yaml

SETTINGS_FILE = os.path.join(ATRAIN_DIR, "settings.txt")


class Settings:
    def __init__(self, cuda_available: bool):
        self.cuda_available = cuda_available

    def __str__(self):
        return str(vars(self))

    def to_dict(self):
        return vars(self)


def load_settings() -> Settings:
    settings_exist = os.path.exists(SETTINGS_FILE)
    settings_correct = True  # We assume the settings are correct

    if (settings_exist and settings_correct):
        with open(SETTINGS_FILE, "r", encoding='utf-8') as settings_file:
            settings_dict = yaml.safe_load(settings_file)
        try:
            settings = Settings(**settings_dict)
        except:
            settings_correct = False

    if not (settings_exist and settings_correct):
        # check if cuda is available
        from torch import cuda
        cuda_available = cuda.is_available()
        settings = Settings(cuda_available=cuda_available)
        write_settings(settings)

    return settings


def write_settings(settings: Settings):
    os.makedirs(ATRAIN_DIR, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding='utf-8') as settings_file:
        yaml.safe_dump(settings.to_dict(), settings_file)
