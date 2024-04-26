from multiprocessing import Queue, Process
from queue import Full
from typing import Literal, List

SERVER_EVENTS = Literal["error", "progress_value" , "progress_max", "task" , "finished" , "wrong_input"]
RUNNING_PROCESSES = []

def stop_all_processes():
    """Terminate all running processes."""
    process : Process
    for process in RUNNING_PROCESSES:
        process.terminate()
        print(f"Terminated {process.name}.")
    RUNNING_PROCESSES.clear()
    print("All processes have been terminated.")

class EventSender:
    def __init__(self, maxsize : int = 10):
        self.listeners : List[Queue]= []
        self.maxsize : int = maxsize

    def stream(self):
        listener = Queue(maxsize=self.maxsize)
        self.listeners.append(listener)
        while True:
            event = listener.get()
            if event == "stop":
                break
            yield event

    def send(self, data, event : SERVER_EVENTS, stop: bool = False):
        event_string = f"event: {event}\ndata: {data}\n\n" if not stop else "stop"
        for i in reversed(range(len(self.listeners))):
            try:
                self.listeners[i].put_nowait(event_string)
            except Full:
                del self.listeners[i]

    def stop(self):
        self.send(data = None, event = None, stop = True)

EVENT_SENDER = EventSender()

def teardown():
    EVENT_SENDER.stop()
    stop_all_processes()