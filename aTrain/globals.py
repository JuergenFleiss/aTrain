import os

USER_DIR = os.path.expanduser("~")
DOCUMENTS_DIR = os.path.join(USER_DIR,"Documents")
ATRAIN_DIR = os.path.join(DOCUMENTS_DIR,"aTrain")
TRANSCRIPT_DIR = os.path.join(ATRAIN_DIR,"transcriptions")
SETTINGS_FILE = os.path.join(ATRAIN_DIR,"settings.txt")
METADATA_FILENAME = "metadata.txt"
TIMESTAMP_FORMAT = "%Y-%m-%d %H-%M-%S"