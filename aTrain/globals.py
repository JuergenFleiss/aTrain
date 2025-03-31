import os
from aTrain_core.globals import ATRAIN_DIR
from aTrain_core.GUI_integration import EventSender

MODELS_DIR = os.path.join(ATRAIN_DIR, "models")
RUNNING_DOWNLOADS = []
RUNNING_TRANSCRIPTIONS = []
EVENT_SENDER = EventSender()
