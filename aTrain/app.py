import argparse

import webview
from flask import Flask
from screeninfo import get_monitors
from wakepy import keep

from .api import api
from .globals import EVENT_SENDER
from aTrain_core.globals import REQUIRED_MODELS, REQUIRED_MODELS_DIR
from .models import start_model_download, stop_all_downloads
from .routes import routes
from .transcription import stop_all_transcriptions

app = Flask(__name__)
app.register_blueprint(routes)
app.register_blueprint(api)


def run_app() -> None:
    """A function that creates creates the application window and runs the app."""
    app_height = int(min([monitor.height for monitor in get_monitors()]) * 0.8)
    app_width = int(min([monitor.width for monitor in get_monitors()]) * 0.8)
    window = webview.create_window("aTrain", app, height=app_height, width=app_width)
    window.events.closed += teardown
    with keep.running():
        webview.start()


def teardown() -> None:
    """A function that is invoked when the application window closes and which terminates all processes that are still running."""
    EVENT_SENDER.end_stream()
    stop_all_transcriptions()
    stop_all_downloads()


def cli() -> None:
    """A function that parses the CLI arguments and runs the application accordingly."""
    parser = argparse.ArgumentParser(
        prog="aTrain", description="A GUI tool to transcribe audio with Whisper"
    )
    parser.add_argument(
        "command",
        choices=["init", "start", "dev"],
        help="Command for aTrain to perform.",
    )
    args = parser.parse_args()

    if args.command == "init":
        for model in REQUIRED_MODELS:
            start_model_download(model=model, models_dir=REQUIRED_MODELS_DIR)

    if args.command == "start":
        print("Running aTrain")
        run_app()

    if args.command == "dev":
        print("Running aTrain in dev mode")
        app.run()
