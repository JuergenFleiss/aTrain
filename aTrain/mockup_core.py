#This is a mockup pipeline that will later be replaced by aTrain_core
from .process import EventSender
import time
import json
import traceback

def transcribe(event_sender : EventSender = EventSender()):
    #----input checking----#
    input_correct = check_inputs()
    if not input_correct:
        event_sender.send("", event="wrong_input")
        return ""
    
    #----running transcription----#
    try:
        transcribe_id = 123
        total_progess_steps = 10
        event_sender.send(total_progess_steps, event="progress_max")
        for i in range(total_progess_steps):
            time.sleep(1)
            print(i)
            event_sender.send(i, event="progress_value")
            if not i % 5:
                event_sender.send(f"Task{i}", event="task")
            if i == 7:
                raise ValueError("something weird happened")
        download_url = f"open/{transcribe_id}"
        event_sender.send(download_url, event="finished")

    except Exception as error:
        traceback_str = traceback.format_exc()
        error = str(error)
        error_data = json.dumps({"error" : error, "traceback" : traceback_str})
        event_sender.send(error_data, event="error")

def check_inputs():
    return True