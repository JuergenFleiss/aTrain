import os
from importlib.resources import files
from pathlib import Path
from typing import Annotated, cast
from unittest.mock import patch

from aTrain_core.globals import ATRAIN_DIR, FLATPAK, REQUIRED_MODELS
from aTrain_core.load_resources import get_model
from platformdirs import user_config_path
from typer import Option, Typer
from wakepy import keep

from aTrain.utils.ports import find_available_port

NICEGUI_STORAGE_PATH = user_config_path() / "aTrain" if FLATPAK else (ATRAIN_DIR / "settings")

with patch.dict(os.environ, NICEGUI_STORAGE_PATH=str(NICEGUI_STORAGE_PATH)):
    from nicegui import ui

    from aTrain.pages import about, archive, faq, models, transcribe  # noqa

cli = Typer(help="CLI for aTrain.")


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
