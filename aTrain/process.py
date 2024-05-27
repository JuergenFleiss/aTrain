from multiprocessing import Process
from flask import Request
from aTrain_core.GUI_integration import EventSender

RUNNING_PROCESSES = []
EVENT_SENDER = EventSender()


def get_inputs(request: Request):
    file = request.form.get('file')
    model = request.form.get('model')
    language = request.form.get('language')
    speaker_detection = True if request.form.get(
        'speaker_detection') else False
    num_speakers = request.form.get("num_speakers")
    device = "GPU" if request.form.get('GPU') else "CPU"
    compute_type = "float16" if request.form.get('float16') else "int8"
    return file, model, language, speaker_detection, num_speakers, device, compute_type


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
