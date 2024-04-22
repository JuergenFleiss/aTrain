#This is a mockup pipeline that will later be replaced by aTrain_core
import time
from .SSE import send_event
from .globals import SERVER_EVENTS

def transcribe():
    transcribe_id = 123
    total_progess_steps = 10
    send_event(total_progess_steps, event=SERVER_EVENTS.progress_total)
    for i in range(total_progess_steps):
        time.sleep(1)
        send_event(i, event=SERVER_EVENTS.progress)
        if not i % 5:
            send_event(f"Task{i}", event=SERVER_EVENTS.task)
    download_url = f"open/{transcribe_id}"
    send_event(download_url, event=SERVER_EVENTS.finished)

def check_inputs():
    return True