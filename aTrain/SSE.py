import zmq
import socket

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))  # Bind to an available port provided by the OS
        return s.getsockname()[1]  # Return the port number assigned

SSE_FRONT_PORT = find_free_port()
SSE_BACK_PORT = find_free_port()

def send_event(data, event : str = "message"):
    sender = zmq.Context().socket(zmq.PUSH)
    sender.connect(f"tcp://localhost:{SSE_FRONT_PORT}")
    event_string = f"event: {event}\ndata: {data}\n\n"
    sender.send_string(event_string)
    
def stream_events():
    print("connected")
    receiver = zmq.Context().socket(zmq.PULL)
    receiver.connect(f"tcp://localhost:{SSE_BACK_PORT}")
    while True:
        event = receiver.recv_string()
        yield event

def start_SSE():
    try:
        context = zmq.Context()
        frontend = context.socket(zmq.PULL)
        frontend.bind(f"tcp://localhost:{SSE_FRONT_PORT}")
        backend = context.socket(zmq.PUSH)
        backend.bind(f"tcp://localhost:{SSE_BACK_PORT}")
        zmq.device(zmq.STREAMER, frontend, backend)
    finally:
        frontend.close()
        backend.close()
        context.term()
