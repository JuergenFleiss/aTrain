import os
import socket
from importlib.resources import files
from pathlib import Path
from typing import Annotated, cast
from unittest.mock import patch

from aTrain_core.globals import ATRAIN_DIR, FLATPAK, REQUIRED_MODELS
from aTrain_core.load_resources import get_model
from platformdirs import user_config_path
from typer import Option, Typer
from wakepy import keep

NICEGUI_STORAGE_PATH = user_config_path() / "aTrain" if FLATPAK else (ATRAIN_DIR / "settings")

with patch.dict(os.environ, NICEGUI_STORAGE_PATH=str(NICEGUI_STORAGE_PATH)):
    from nicegui import ui

    from aTrain.pages import about, archive, faq, models, transcribe  # noqa

cli = Typer(help="CLI for aTrain.")


def find_available_port(start_port: int) -> int:
    for port in range(start_port, start_port + 1000):
        if is_port_available(port):
            return port
    raise RuntimeError(f"No available port found starting at {start_port}")


def is_port_available(port: int) -> bool:
    wildcard_host = "0.0.0.0"  # noqa: S104 - probing a bind address, not listening on it
    for host in ("127.0.0.1", wildcard_host):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((host, port))
            except OSError:
                return False
    return True


@cli.command()
def init():
    """Download all required model for aTrain."""
    for model in REQUIRED_MODELS:
        get_model(model=model)


@cli.command()
def start(
    native: Annotated[bool, Option(help="Run in a native window")] = True,
    reload: Annotated[bool, Option(help="Reload on code change")] = False,
    port: Annotated[
        int, Option(help="Starting port for the web server; next free port is used")
    ] = 8080,
):
    """Start aTrain."""
    print("Running aTrain")
    selected_port = find_available_port(port)
    if selected_port != port:
        print(f"Port {port} is busy, using {selected_port} instead")
    if FLATPAK:
        ui.run(
            native=native,
            reload=reload,
            port=selected_port,
            title="aTrain",
            favicon=cast(Path, files("aTrain") / "static" / "favicon.ico"),
            window_size=(1280, 720) if native else None,
        )
    else:
        with keep.running():
            ui.run(
                native=native,
                reload=reload,
                port=selected_port,
                title="aTrain",
                favicon=cast(Path, files("aTrain") / "static" / "favicon.ico"),
                window_size=(1280, 720) if native else None,
            )
