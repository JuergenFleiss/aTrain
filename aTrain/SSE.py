from queue import Queue
from blinker import signal

EVENT_SIGNAL = signal("SSE")
EVENT_QUEUE = Queue(maxsize=5)
STOP_QUEUE = Queue(maxsize=1)

@EVENT_SIGNAL.connect
def add_to_EVENT_QUEUE(data):
    EVENT_QUEUE.put(data)

def send_event(data, event : str = None):
    event = event if event else "data"
    event_string = f"{event}: {data}\n\n"
    EVENT_SIGNAL.send(event_string)

def stream_events():
    while STOP_QUEUE.empty():
        try:
            event = EVENT_QUEUE.get_nowait()
            yield event
        except:
            continue

def stop_SSE():
    STOP_QUEUE.put("stop")