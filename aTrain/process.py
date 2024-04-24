from multiprocessing import Queue
from queue import Empty, Full
from typing import Literal, List

SERVER_EVENTS = Literal["error", "progress_value" , "progress_max", "task" , "finished" , "wrong_input"]
RUNNING_PROCESSES = []

def kill_all_processes():
    """Terminate all running processes."""
    for process in RUNNING_PROCESSES:
        process.terminate()
        print(f"Terminated {process.name}.")
    RUNNING_PROCESSES.clear()
    print("All processes have been terminated.")

class EventSender:
    def __init__(self, maxsize = 10):
        self.listeners : List[Queue]= []
        self.maxsize = maxsize
        self.stopper : Queue = Queue(maxsize=1)

    def stream(self):
        listener = Queue(maxsize=self.maxsize)
        self.listeners.append(listener)
        while self.stopper.empty():
            try:
                event = listener.get_nowait()
                yield event
            except Empty:
                continue

    def send(self, data, event : SERVER_EVENTS):
        event_string = f"event: {event}\ndata: {data}\n\n"
        for i in reversed(range(len(self.listeners))):
            try:
                self.listeners[i].put_nowait(event_string)
            except Full:
                del self.listeners[i]

    def stop(self):
        self.stopper.put("stop")

EVENT_SENDER = EventSender()

