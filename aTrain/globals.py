from aTrain_core.GUI_integration import EventSender
from aTrain_core.globals import ATRAIN_DIR
import os

MODELS_DIR = os.path.join(ATRAIN_DIR, "models")
RUNNING_DOWNLOADS = []
RUNNING_TRANSCRIPTIONS = []
EVENT_SENDER = EventSender()
