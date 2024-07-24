import os
import shutil
import yaml
from showinfm import show_in_file_manager
from importlib.resources import files
from aTrain_core.globals import TRANSCRIPT_DIR, METADATA_FILENAME


def read_archive():
    os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
    all_file_directories = [directory.name for directory in os.scandir(
        TRANSCRIPT_DIR) if directory.is_dir()]
    all_file_directories.sort(reverse=True)
    all_metadata = []
    for directory_name in all_file_directories:
        metadata_file_path = os.path.join(
            TRANSCRIPT_DIR, directory_name, METADATA_FILENAME)
        if os.path.exists(metadata_file_path):
            with open(metadata_file_path, "r", encoding="utf-8") as metadata_file:
                metadata = yaml.safe_load(metadata_file)
                metadata["file_id"] = directory_name
            all_metadata.append(metadata)
        else:
            metadata = {
                "file_id": directory_name,
                "filename": directory_name[20:] if len(directory_name) > 20 else "-",
                "timestamp": directory_name[:20] if len(directory_name) >= 20 else "-"
            }
            all_metadata.append(metadata)
    return all_metadata


def delete_transcription(file_id):
    file_id = "" if file_id == "all" else file_id
    directory_name = os.path.join(TRANSCRIPT_DIR, file_id)
    if os.path.exists(directory_name):
        shutil.rmtree(directory_name)
    if not os.path.exists(TRANSCRIPT_DIR):
        os.makedirs(TRANSCRIPT_DIR, exist_ok=True)


def open_file_directory(file_id):
    file_id = "" if file_id == "all" else file_id
    directory_name = os.path.join(TRANSCRIPT_DIR, file_id)
    if os.path.exists(directory_name):
        show_in_file_manager(directory_name)


def load_faqs():
    faq_path = str(files("aTrain.static").joinpath("faq.yaml"))
    with open(faq_path, "r", encoding='utf-8') as faq_file:
        faqs = yaml.safe_load(faq_file)
    return faqs
