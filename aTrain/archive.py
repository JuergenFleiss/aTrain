import os
import shutil
from showinfm import show_in_file_manager
import yaml
from datetime import datetime

APP_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(APP_DIR,"models")
USER_DIR = os.path.expanduser("~")
DOCUMENTS_DIR = os.path.join(USER_DIR,"Documents")
ATRAIN_DIR = os.path.join(DOCUMENTS_DIR,"aTrain")
TRANSCRIPT_DIR = os.path.join(ATRAIN_DIR,"transcriptions")
METADATA_FILENAME = "metadata.txt"
TIMESTAMP_FORMAT = "%Y-%m-%d %H-%M-%S"

def read_archive():
    os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
    all_file_directories = [ directory.name for directory in os.scandir(TRANSCRIPT_DIR) if directory.is_dir() ]
    all_file_directories.sort(reverse=True)
    all_metadata = []
    for directory_name in all_file_directories:
        metadata_file_path = os.path.join(TRANSCRIPT_DIR,directory_name,METADATA_FILENAME)
        if os.path.exists(metadata_file_path):
            with open(metadata_file_path, "r", encoding="utf-8") as metadata_file:
                metadata = yaml.safe_load(metadata_file)
                metadata["file_id"] = directory_name
            all_metadata.append(metadata)
        else:
            metadata = {
                "file_id" : directory_name,
                "filename" : directory_name[20:] if len(directory_name)>20 else "-",
                "timestamp" : directory_name[:20] if len(directory_name)>=20 else "-"
            }
            all_metadata.append(metadata)
    return all_metadata

def create_metadata(file_id, filename, audio_duration, model, language, speaker_detection, num_speakers, device, timestamp):
    metadata_file_path = os.path.join(TRANSCRIPT_DIR,file_id,METADATA_FILENAME)
    metadata = {
        "file_id" : file_id,
        "filename" : filename,
        "audio_duration" : audio_duration,
        "model" : model,
        "language" : language,
        "speaker_detection" : speaker_detection,
        "num_speakers" : num_speakers,
        "device": device,
        "timestamp": timestamp 
        }
    with open(metadata_file_path,"w", encoding="utf-8") as metadata_file:
        yaml.dump(metadata, metadata_file)

def read_metadata(file_id):
    metadata_file_path = os.path.join(TRANSCRIPT_DIR,file_id,METADATA_FILENAME)
    with open(metadata_file_path,"r", encoding="utf-8") as metadata_file:
        metadata = yaml.safe_load(metadata_file)
    filename = metadata["filename"]
    model = metadata["model"]
    language = metadata["language"]
    speaker_detection = metadata["speaker_detection"]
    num_speakers = metadata["num_speakers"]
    return filename, model, language, speaker_detection, num_speakers

def add_processing_time_to_metadata(file_id):
    metadata_file_path = os.path.join(TRANSCRIPT_DIR,file_id,METADATA_FILENAME)
    with open(metadata_file_path, "r", encoding="utf-8") as metadata_file:
        metadata = yaml.safe_load(metadata_file)
    timestamp = metadata["timestamp"]
    start_time = datetime.strptime(timestamp,TIMESTAMP_FORMAT)
    stop_time = timestamp = datetime.now()
    processing_time = stop_time-start_time
    metadata["processing_time"] = int(processing_time.total_seconds())
    with open(metadata_file_path, "w", encoding="utf-8") as metadata_file:
        yaml.dump(metadata,metadata_file)

def delete_transcription(file_id):
    file_id = "" if file_id == "all" else file_id
    directory_name = os.path.join(TRANSCRIPT_DIR,file_id)
    if os.path.exists(directory_name):    
        shutil.rmtree(directory_name)
    if not os.path.exists(TRANSCRIPT_DIR):
        os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
    
def open_file_directory(file_id):
    file_id = "" if file_id == "all" else file_id
    directory_name = os.path.join(TRANSCRIPT_DIR,file_id)
    if os.path.exists(directory_name):
        show_in_file_manager(directory_name)

if __name__ == "__main__":
    ...