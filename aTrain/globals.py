import os
from importlib.resources import files
from aTrain_core.globals import ATRAIN_DIR
from aTrain_core.GUI_integration import EventSender

MODELS_DIR = os.path.join(ATRAIN_DIR, "models")
RUNNING_DOWNLOADS = []
RUNNING_TRANSCRIPTIONS = []
EVENT_SENDER = EventSender()
REQUIRED_MODELS_DIR = files("aTrain") / "required_models"
REQUIRED_MODELS = ["diarize", "large-v3-turbo"]
