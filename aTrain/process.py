from multiprocessing import Process
from flask import Request
from aTrain_core.GUI_integration import EventSender
from aTrain_core.check_inputs import check_inputs_transcribe
from aTrain_core.globals import TIMESTAMP_FORMAT
from aTrain_core.transcribe import transcribe
from aTrain_core.outputs import create_file_id
from datetime import datetime
import traceback

RUNNING_PROCESSES = []
EVENT_SENDER = EventSender()


def start_process(request: Request):
    inputs = get_inputs(request=request)
    transciption = Process(target=try_to_transcribe,
                           args=(inputs, EVENT_SENDER), daemon=True)
    transciption.start()
    RUNNING_PROCESSES.append(transciption)


def get_inputs(request: Request):
    inputs = dict(request.form)
    inputs["speaker_detection"] = True if "speaker_detection" in inputs else False
    inputs["device"] = "GPU" if 'GPU' in inputs else "CPU"
    inputs["compute_type"] = "float16" if 'float16' in inputs else "int8"
    return inputs


def try_to_transcribe(inputs: dict, event_sender: EventSender):
    try:
        check_inputs_transcribe(
            file=inputs["file"], model=inputs["model"], language=inputs["language"], device=inputs["device"])
        timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
        file_id = create_file_id(inputs["file"], timestamp)
        transcribe(inputs["file"], file_id, inputs["model"], inputs["language"], inputs["speaker_detection"],
                   inputs["num_speakers"], inputs["device"], inputs["compute_type"], timestamp, event_sender)
    except Exception as error:
        traceback_str = traceback.format_exc()
        event_sender.error_info(str(error), traceback_str)


def stop_all_processes():
    """Terminate all running processes."""
    process: Process
    for process in RUNNING_PROCESSES:
        process.terminate()
    RUNNING_PROCESSES.clear()
    print("All processes have been terminated.")


def teardown():
    EVENT_SENDER.end_stream()
    stop_all_processes()
