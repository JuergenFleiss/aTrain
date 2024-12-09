import os
import sys
import traceback
from datetime import datetime
from io import BytesIO
from threading import Thread

from aTrain_core.check_inputs import check_inputs_transcribe
from aTrain_core.globals import REQUIRED_MODELS_DIR, TIMESTAMP_FORMAT
from aTrain_core.GUI_integration import EventSender
from aTrain_core.outputs import create_directory, create_file_id, write_logfile
from aTrain_core.transcribe import transcribe
from flask import Request
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from .globals import EVENT_SENDER, RUNNING_TRANSCRIPTIONS


def create_thread(request: Request) -> None:
    """This function executes the transcription in a seperate thread."""
    settings, file = get_inputs(request=request)
    transciption = StoppableThread(
        target=start_transcription,
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
    settings["compute_type"] = (
        "float16"
        if "float16" in settings
        else "float32"
        if "float32" in settings
        else "int8"
    )
    settings["initial_prompt"] = (
        settings["initial_prompt"]
        if len(settings["initial_prompt"].strip()) > 0
        else None
    )
    return settings


def start_transcription(
    settings: dict, file_name: str, file_content: bytes, event_sender: EventSender
) -> None:
    """A function that checks the inputs for the transcription and then transcribes the audio file."""
    try:
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
            settings["initial_prompt"],
            event_sender,
            REQUIRED_MODELS_DIR,
        )
        event_sender.finished_info()
    except Exception as error:
        traceback_str = traceback.format_exc()
        event_sender.error_info(str(error), traceback_str)


def stop_all_transcriptions() -> None:
    """A function that terminates all running transcription processes."""
    thread: StoppableThread
    for thread in RUNNING_TRANSCRIPTIONS:
        thread.stop()
    RUNNING_TRANSCRIPTIONS.clear()


class StoppableThread(Thread):
    def __init__(self, target=None, args=(), kwargs=None, daemon: bool | None = None):
        Thread.__init__(self, target=target, args=args, kwargs=kwargs)
        self.killed = False

    def start(self):
        self.__run_backup = self.run
        self.run = self.__run
        Thread.start(self)

    def __run(self):
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup

    def globaltrace(self, frame, event, arg):
        if event == "call":
            return self.localtrace
        else:
            return None

    def localtrace(self, frame, event, arg):
        if self.killed:
            if event == "line":
                raise SystemExit()
        return self.localtrace

    def stop(self):
        self.killed = True
