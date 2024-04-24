#This is a mockup pipeline that will later be replaced by aTrain_core
import time
from .process import EventSender

def transcribe(event_sender : EventSender = EventSender()):
    transcribe_id = 123
    total_progess_steps = 10
    event_sender.send(total_progess_steps, event="progress_max")
    for i in range(total_progess_steps):
        time.sleep(1)
        print(i)
        event_sender.send(i, event="progress_value")
        if not i % 5:
            event_sender.send(f"Task{i}", event="task")
    download_url = f"open/{transcribe_id}"
    event_sender.send(download_url, event="finished")

def check_inputs():
    return True