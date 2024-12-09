import os
import traceback
from datetime import datetime
from io import BytesIO
from multiprocessing import Process

from aTrain_core.check_inputs import check_inputs_transcribe
from aTrain_core.globals import TIMESTAMP_FORMAT
from aTrain_core.GUI_integration import EventSender
from aTrain_core.outputs import create_directory, create_file_id, write_logfile
from aTrain_core.transcribe import transcribe
from flask import Request
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from .globals import EVENT_SENDER, RUNNING_TRANSCRIPTIONS
from aTrain_core.globals import REQUIRED_MODELS_DIR


def start_process(request: Request) -> None:
    """This function executes the transcription in a seperate process."""
    settings, file = get_inputs(request=request)
    transciption = Process(
        target=try_to_transcribe,
        args=(settings, file.filename, file.stream.read(), EVENT_SENDER),
        daemon=True,
    )
    transciption.start()
    RUNNING_TRANSCRIPTIONS.append(transciption)


def get_inputs(request: Request) -> tuple[dict, FileStorage]:
    """This function extracts the file and form data from the flask request and returns them."""
    file = request.files["file"]
    settings = dict(request.form)
    settings = resolve_boolean_inputs(settings)
    print(settings)
    return settings, file


def resolve_boolean_inputs(settings: dict) -> dict:
    """This function checks if boolean inputs are present and replaces them with their respective values."""
    settings["speaker_detection"] = True if "speaker_detection" in settings else False
    settings["device"] = "GPU" if "GPU" in settings else "CPU"
    settings["compute_type"] = "float16" if "float16" in settings else "int8"
    settings['initial_prompt'] = settings['initial_prompt'] if len(settings["initial_prompt"].strip()) > 0 else None
    return settings


def try_to_transcribe(
    settings: dict, file_name: str, file_content: bytes, event_sender: EventSender
) -> None:
    """A function that calls aTrain_core and handles errors if they happen."""
    try:
        start_transcription(settings, file_name, file_content, event_sender)
        event_sender.finished_info()
    except Exception as error:
        traceback_str = traceback.format_exc()
        event_sender.error_info(str(error), traceback_str)


def start_transcription(
    settings: dict, file_name: str, file_content: bytes, event_sender: EventSender
) -> None:
    """A function that checks the inputs for the transcription and then transcribes the audio file."""

    timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)

    dir_name = os.path.dirname(file_name)
    file_base_name = os.path.basename(file_name)

    # Secure the base name (remove unsafe characters)
    secure_file_base_name = secure_filename(file_base_name)

    # Join the directory path with the secure base name to get the full path
    file_name_secure = os.path.join(dir_name, secure_file_base_name)

    file_id = create_file_id(file_name_secure, timestamp)
    create_directory(file_id)
    write_logfile(f"File ID created: {file_id}", file_id)

    check_inputs_transcribe(
        file=file_name_secure,
        model=settings["model"],
        language=settings["language"],
        device=settings["device"],
    )

    transcribe(
        BytesIO(file_content),
        file_id,
        settings["model"],
        settings["language"],
        settings["speaker_detection"],
        settings["num_speakers"],
        settings["device"],
        settings["compute_type"],
        timestamp,
        file_name,  # original file path
        settings['initial_prompt'],
        event_sender,
        REQUIRED_MODELS_DIR,
    )


def stop_all_transcriptions() -> None:
    """A function that terminates all running transcription processes."""
    process: Process
    for process in RUNNING_TRANSCRIPTIONS:
        process.terminate()
    RUNNING_TRANSCRIPTIONS.clear()
