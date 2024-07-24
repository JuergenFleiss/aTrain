from .transcription import RUNNING_PROCESSES
import os
from showinfm import show_in_file_manager
from aTrain_core.globals import ATRAIN_DIR
from aTrain_core.load_resources import download_all_resources, get_model, load_model_config_file
from multiprocessing import Process


MODELS_DIR = os.path.join(ATRAIN_DIR, "models")


def read_downloaded_models() -> list:
    os.makedirs(MODELS_DIR, exist_ok=True)
    all_file_directories = [directory.name for directory in os.scandir(
        MODELS_DIR) if directory.is_dir()]
    all_file_directories.sort(reverse=True)
    all_downloaded_models = []
    for directory_name in all_file_directories:
        directory_path = os.path.join(MODELS_DIR, directory_name)
        for file in os.listdir(directory_path):
            # model only with .bin file available
            if file.endswith('.bin'):
                all_downloaded_models.append(directory_name)
                break
    return all_downloaded_models


def read_model_metadata() -> list:
    all_models = list(load_model_config_file().keys())
    downloaded_models = read_downloaded_models()
    all_models_metadata = []

    for model in all_models:
        model_info = {
            "model": model,
            "downloaded": model in downloaded_models
        }
        all_models_metadata.append(model_info)

    all_models_metadata = sorted(
        all_models_metadata, key=lambda x: x["downloaded"], reverse=True)

    return all_models_metadata


def model_languages(model: str) -> dict:

    languages = {
        "auto-detect": "Detect automatically",
        "af": "Afrikaans",
        "ar": "Arabic",
        "hy": "Armenian",
        "az": "Azerbaijani",
        "be": "Belarusian",
        "bs": "Bosnian",
        "bg": "Bulgarian",
        "ca": "Catalan",
        "zh": "Chinese",
        "hr": "Croatian",
        "cs": "Czech",
        "da": "Danish",
        "nl": "Dutch",
        "en": "English",
        "et": "Estonian",
        "fi": "Finnish",
        "fr": "French",
        "gl": "Galician",
        "de": "German",
        "el": "Greek",
        "he": "Hebrew",
        "hi": "Hindi",
        "hu": "Hungarian",
        "is": "Icelandic",
        "id": "Indonesian",
        "it": "Italian",
        "ja": "Japanese",
        "kn": "Kannada",
        "kk": "Kazakh",
        "ko": "Korean",
        "lv": "Latvian",
        "lt": "Lithuanian",
        "mk": "Macedonian",
        "ms": "Malay",
        "mr": "Marathi",
        "mi": "Maori",
        "ne": "Nepali",
        "no": "Norwegian",
        "fa": "Persian",
        "pl": "Polish",
        "pt": "Portuguese",
        "ro": "Romanian",
        "ru": "Russian",
        "sr": "Serbian",
        "sk": "Slovak",
        "sl": "Slovenian",
        "es": "Spanish",
        "sw": "Swahili",
        "sv": "Swedish",
        "tl": "Tagalog",
        "ta": "Tamil",
        "th": "Thai",
        "tr": "Turkish",
        "uk": "Ukrainian",
        "ur": "Urdu",
        "vi": "Vietnamese",
        "cy": "Welsh"}

    models = load_model_config_file()

    if models[model]["type"] == "distil":
        lang_from_config = models[model]["language"]
        languages = {lang_from_config: languages[lang_from_config]}

    return languages

    #     metadata_file_path = os.path.join(MODELS_DIR,directory_name)
    #     if os.path.exists(metadata_file_path):
    #         with open(metadata_file_path, "r", encoding="utf-8") as metadata_file:
    #             metadata = yaml.safe_load(metadata_file)
    #             metadata["file_id"] = directory_name
    #         all_metadata.append(metadata)
    #     else:
    #         metadata = {
    #             "file_id" : directory_name,
    #             "filename" : directory_name[20:] if len(directory_name)>20 else "-",
    #             "timestamp" : directory_name[:20] if len(directory_name)>=20 else "-"
    #         }
    #         all_metadata.append(metadata)
    # return all_metadata


def open_model_dir(model: str) -> None:
    model = "" if model == "all" else model
    directory_name = os.path.join(MODELS_DIR, model)
    if os.path.exists(directory_name):
        show_in_file_manager(directory_name)


def start_model_download(model: str) -> None:
    model_download = Process(target=download_model,
                             kwargs={"model": model}, daemon=True)
    model_download.start()
    RUNNING_PROCESSES.append(model_download)
    model_download.join()


def download_model(model: str) -> None:
    if model == "all":
        download_all_resources()
    else:
        _ = get_model(model)
    print("Model download completed")
