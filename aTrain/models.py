import os
import traceback
import urllib.error
import urllib.request

from aTrain_core.globals import MODELS_DIR, REQUIRED_MODELS, REQUIRED_MODELS_DIR
from aTrain_core.GUI_integration import EventSender
from aTrain_core.load_resources import get_model, load_model_config_file, remove_model
from showinfm import show_in_file_manager

from .globals import EVENT_SENDER, RUNNING_DOWNLOADS
from .stoppable_thread import StoppableThread


def read_downloaded_models() -> list:
    directories_to_search = [MODELS_DIR, REQUIRED_MODELS_DIR]
    all_downloaded_models = []

    for directory in directories_to_search:
        os.makedirs(directory, exist_ok=True)
        all_file_directories = [
            dir_entry.name for dir_entry in os.scandir(directory) if dir_entry.is_dir()
        ]
        all_file_directories.sort(reverse=True)

        for directory_name in all_file_directories:
            directory_path = os.path.join(directory, directory_name)
            for file in os.listdir(directory_path):
                # model only with .bin file available
                if file.endswith(".bin") and directory_name in list(
                    load_model_config_file().keys()
                ):
                    all_downloaded_models.append(directory_name)
                    break

    return all_downloaded_models


def read_model_metadata() -> list:
    model_metadata = load_model_config_file()
    all_models = list(model_metadata.keys())
    downloaded_models = read_downloaded_models()
    all_models_metadata = []

    for model in all_models:
        model_info = {
            "model": model,
            "size": model_metadata[model]["model_bin_size_human"],
            "downloaded": model in downloaded_models,
        }
        all_models_metadata.append(model_info)

    all_models_metadata = sorted(
        all_models_metadata, key=lambda x: x["downloaded"], reverse=True
    )

    return all_models_metadata


def model_languages(model: str) -> dict:
    languages = {
        "auto-detect": "Detect automatically",
        "en": "english",
        "zh": "chinese",
        "de": "german",
        "es": "spanish",
        "ru": "russian",
        "ko": "korean",
        "fr": "french",
        "ja": "japanese",
        "pt": "portuguese",
        "tr": "turkish",
        "pl": "polish",
        "ca": "catalan",
        "nl": "dutch",
        "ar": "arabic",
        "sv": "swedish",
        "it": "italian",
        "id": "indonesian",
        "hi": "hindi",
        "fi": "finnish",
        "vi": "vietnamese",
        "he": "hebrew",
        "uk": "ukrainian",
        "el": "greek",
        "ms": "malay",
        "cs": "czech",
        "ro": "romanian",
        "da": "danish",
        "hu": "hungarian",
        "ta": "tamil",
        "no": "norwegian",
        "th": "thai",
        "ur": "urdu",
        "hr": "croatian",
        "bg": "bulgarian",
        "lt": "lithuanian",
        "la": "latin",
        "mi": "maori",
        "ml": "malayalam",
        "cy": "welsh",
        "sk": "slovak",
        "te": "telugu",
        "fa": "persian",
        "lv": "latvian",
        "bn": "bengali",
        "sr": "serbian",
        "az": "azerbaijani",
        "sl": "slovenian",
        "kn": "kannada",
        "et": "estonian",
        "mk": "macedonian",
        "br": "breton",
        "eu": "basque",
        "is": "icelandic",
        "hy": "armenian",
        "ne": "nepali",
        "mn": "mongolian",
        "bs": "bosnian",
        "kk": "kazakh",
        "sq": "albanian",
        "sw": "swahili",
        "gl": "galician",
        "mr": "marathi",
        "pa": "punjabi",
        "si": "sinhala",
        "km": "khmer",
        "sn": "shona",
        "yo": "yoruba",
        "so": "somali",
        "af": "afrikaans",
        "oc": "occitan",
        "ka": "georgian",
        "be": "belarusian",
        "tg": "tajik",
        "sd": "sindhi",
        "gu": "gujarati",
        "am": "amharic",
        "yi": "yiddish",
        "lo": "lao",
        "uz": "uzbek",
        "fo": "faroese",
        "ht": "haitian creole",
        "ps": "pashto",
        "tk": "turkmen",
        "nn": "nynorsk",
        "mt": "maltese",
        "sa": "sanskrit",
        "lb": "luxembourgish",
        "my": "myanmar",
        "bo": "tibetan",
        "tl": "tagalog",
        "mg": "malagasy",
        "as": "assamese",
        "tt": "tatar",
        "haw": "hawaiian",
        "ln": "lingala",
        "ha": "hausa",
        "ba": "bashkir",
        "jw": "javanese",
        "su": "sundanese",
        "yue": "cantonese",
    }

    models = load_model_config_file()

    if models[model]["type"] == "distil":
        lang_from_config = models[model]["language"]
        languages = {lang_from_config: languages[lang_from_config]}

    return languages


def open_model_dir(model: str, models_dir=MODELS_DIR) -> None:
    """A function that opens the directory where a given model is stored."""
    model = "" if model == "all" else model
    directory_name = os.path.join(models_dir, model)
    if os.path.exists(directory_name):
        show_in_file_manager(directory_name)


def start_model_download(model: str, models_dir=MODELS_DIR) -> None:
    """A function that starts the download of a model in a separate process."""
    if model in REQUIRED_MODELS:
        models_dir = REQUIRED_MODELS_DIR

    model_download = StoppableThread(
        target=try_to_download_model,
        kwargs={"model": model, "event_sender": EVENT_SENDER, "models_dir": models_dir},
        daemon=True,
    )
    model_download.start()
    RUNNING_DOWNLOADS.append((model_download, model))
    model_download.join()
    RUNNING_DOWNLOADS.remove((model_download, model))


def try_to_download_model(
    model: str, event_sender: EventSender, models_dir=None
) -> None:
    """A function that tries to download the specified model and sends any occurring errors to the frontend."""

    if models_dir is None:
        models_dir = MODELS_DIR
    try:
        check_internet()
        get_model(model, event_sender, models_dir, REQUIRED_MODELS_DIR)
        event_sender.finished_info()
    except Exception as error:
        traceback_str = traceback.format_exc()
        event_sender.error_info(str(error), traceback_str)
        remove_model(model)


def check_internet():
    """A function to check whether the user is connected to the internet."""
    try:
        urllib.request.urlopen("https://huggingface.co", timeout=1)
    except urllib.error.URLError:
        raise ConnectionError(
            "We cannot reach Hugging Face. Most likely you are not connected to the internet."
        )


def stop_all_downloads() -> None:
    """A function that terminates all running download processes."""
    download: StoppableThread
    for download, model in RUNNING_DOWNLOADS:
        download.stop()
        download.join()
        remove_model(model)
    RUNNING_DOWNLOADS.clear()
    EVENT_SENDER.finished_info()
