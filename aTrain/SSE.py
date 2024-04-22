import zmq
import socket

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))  # Bind to an available port provided by the OS
        return s.getsockname()[1]  # Return the port number assigned

SSE_SEND_URL = f"tcp://localhost:{find_free_port()}"
SSE_RECV_URL = f"tcp://localhost:{find_free_port()}"

def send_event(data, event : str = "message"):
    sender = zmq.Context().socket(zmq.PUSH)
    sender.connect(SSE_SEND_URL)
    event_string = f"event: {event}\ndata: {data}\n\n"
    sender.send_string(event_string)
    
def stream_events():
    print("connected")
    receiver = zmq.Context().socket(zmq.PULL)
    receiver.connect(SSE_RECV_URL)
    while True:
        event = receiver.recv_string()
        yield event

def start_SSE():
    try:
        context = zmq.Context()
        frontend = context.socket(zmq.PULL)
        frontend.bind(SSE_SEND_URL)
        backend = context.socket(zmq.PUSH)
        backend.bind(SSE_RECV_URL)
        zmq.device(zmq.STREAMER, frontend, backend)
    finally:
        frontend.close()
        backend.close()
        context.term()
