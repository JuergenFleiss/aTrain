#This is a mockup pipeline that will later be replaced by aTrain_core
import time
from .SSE import send_event

def transcribe():
    for i in range(500):
        time.sleep(1)
        send_event(i, event="test")
