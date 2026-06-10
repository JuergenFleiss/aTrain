import socket
from contextlib import nullcontext

from aTrain import app as atrain_app


def test_find_available_port_skips_busy_ports(monkeypatch):
    bound_addresses = []

    class FakeSocket:
        def __init__(self, *args, **kwargs):
            self.address = None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def bind(self, address):
            bound_addresses.append(address)
            if address == ("127.0.0.1", 8080):
                raise OSError("busy")
            self.address = address

    monkeypatch.setattr(socket, "socket", lambda *args, **kwargs: FakeSocket())

    assert atrain_app.find_available_port(8080) == 8081
    assert bound_addresses == [
        ("127.0.0.1", 8080),
        ("127.0.0.1", 8081),
        ("0.0.0.0", 8081),  # noqa: S104 - test fixture for wildcard bind probing
    ]


def test_start_passes_resolved_port_to_nicegui(monkeypatch):
    captured = {}

    monkeypatch.setattr(atrain_app, "FLATPAK", False)
    monkeypatch.setattr(atrain_app.keep, "running", lambda: nullcontext())
    monkeypatch.setattr(atrain_app, "find_available_port", lambda start_port: 8091)
    monkeypatch.setattr(
        atrain_app.ui,
        "run",
        lambda **kwargs: captured.update(kwargs),
    )

    atrain_app.start(native=False, reload=False, port=8090)

    assert captured["port"] == 8091
    assert captured["native"] is False
    assert captured["reload"] is False
