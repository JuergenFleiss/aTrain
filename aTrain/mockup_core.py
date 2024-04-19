#This is a mockup pipeline that will later be replaced by aTrain_core
import time
from .SSE import send_event
from .globals import SERVER_EVENTS

def transcribe():
    for i in range(500):
        time.sleep(1)
        print(i)
        send_event(i, event=SERVER_EVENTS.task)

def check_inputs():
    return True