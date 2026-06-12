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
    show: Annotated[bool, Option(help="If no-native, open Browser tab.")] = True,
    host: Annotated[str, Option(help="Which IP to bind to (defaults to '127.0.0.1 in native mode, otherwise '0.0.0.0').")] = None,
    port: Annotated[int, Option(help="Which port to bind to  (default: 8080 in no-native mode, and an automatically determined open port in native mode).")] = None
):
    """Start aTrain."""
    print("Running aTrain")
    if FLATPAK:
        ui_run(native, reload, show, host, port)
    else:
        with keep.running():
            ui_run(native, reload, show, host, port)

def ui_run(native: bool, reload: bool, show: bool, host: str, port: int):
    ui.run(
            native=native,
            reload=reload,
            title="aTrain",
            favicon=cast(Path, files("aTrain") / "static" / "favicon.ico"),
            window_size=(1280, 720) if native else None,
            show=show,
            host=host,
            port=port,
        )
