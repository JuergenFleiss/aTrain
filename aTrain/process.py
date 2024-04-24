from multiprocessing import queues, get_context
from queue import Empty
from typing import Literal

SERVER_EVENTS = Literal["error", "progress_value" , "progress_max", "task" , "finished" , "wrong_input"]

class EventQueue(queues.Queue):
    def __init__(self, *args, **kwargs):
        ctx = get_context()  # Get the default context
        super().__init__(ctx=ctx, *args, **kwargs)  # Pass the context to Queue

    def send(self, data, event : SERVER_EVENTS):
        event_string = f"event: {event}\ndata: {data}\n\n"
        try:
            self.put_nowait(event_string)
        except Exception as error:
            print("Encountered an error:", error)

event_queue = EventQueue()
stop_queue = EventQueue(maxsize=1)
running_processes = []

def stream_events():
    while stop_queue.empty():
        try:
            event = event_queue.get_nowait()
            yield event
        except Empty:
            continue

def stop_stream():
    stop_queue.put("stop")

def kill_all_processes():
    """Terminate all running processes."""
    for process in running_processes:
        process.terminate()
        print(f"Terminated {process.name}.")
    running_processes.clear()
    print("All processes have been terminated.")

