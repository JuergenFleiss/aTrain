from queue import Queue, Full, Empty
from blinker import signal

def send_event(data, event : str = "message", channel = "global"):
    event_string = f"event: {event}\ndata: {data}\n\n"
    event_signal = signal(channel)
    event_signal.send(event_string)

def stream_events(channel = "global", queue_size = 0):
    event_queue = Queue(maxsize=queue_size)
    event_signal = signal(channel)

    stop_queue = Queue(maxsize=1)
    stop_signal = signal(f"stop_{channel}")

    def add_to_event_queue(data):
        try:
            event_queue.put_nowait(data)
        except Full:
            stop_signal.send("stop")
            event_signal.disconnect(add_to_event_queue)

    event_signal.connect(add_to_event_queue)

    def add_to_stop_queue(data):
        try:
            stop_queue.put_nowait(data)
        except Full:
            stop_signal.disconnect(add_to_stop_queue)

    stop_signal.connect(add_to_stop_queue)

    while stop_queue.empty():
        try:
            event = event_queue.get_nowait()
            yield event
        except Empty:
            continue

def stop_SSE(channel = "global"):
    stop_signal = signal(f"stop_{channel}")
    stop_signal.send("stop")