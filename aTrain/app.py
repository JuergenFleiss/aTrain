from .utils import read_archive, delete_transcription, open_file_directory, open_model_dir, load_faqs, read_downloaded_models, download_mod
from .version import __version__
from .settings import load_settings
from .process import EVENT_SENDER, stop_all_processes, teardown, start_process
from aTrain_core.load_resources import remove_model, load_model_config_file
from flask import Flask, render_template, redirect, Response, url_for, request
from screeninfo import get_monitors
import webview
from wakepy import keep
import time
import argparse


# -----Setup------#
app = Flask(__name__)


@app.template_filter
def format_duration(duration):
    return time.strftime("%Hh %Mm %Ss", time.gmtime(duration))


@app.context_processor
def set_globals():
    return dict(version=__version__)


# -----Routes------#
@app.get("/")
def home():
    return render_template("pages/transcribe.html", settings=load_settings())


@app.get("/archive")
def archive():
    return render_template("pages/archive.html", archive_data=read_archive())


@app.get("/faq")
def faq():
    return render_template("pages/faq.html", faqs=load_faqs())


@app.get("/model_manager")
def model_manager():
    return render_template("pages/model_manager.html", models=list(load_model_config_file().keys()))


@app.post("/start_transcription")
def start_transcription():
    start_process(request)
    return ""


@app.route("/stop_transcription")
def stop_transcription():
    stop_all_processes()
    return redirect(url_for("home"))


@app.get("/SSE")
def SSE():
    return Response(EVENT_SENDER.stream(), mimetype="text/event-stream")


@app.route('/open_directory/<file_id>')
def open_directory(file_id):
    open_file_directory(file_id)
    return ""


@app.route("/delete_directory/<file_id>")
def delete_directory(file_id):
    delete_transcription(file_id)
    return render_template("pages/archive.html", archive_data=read_archive(), only_content=True)


@app.route('/open_model_directory/<model>')
def open_model_directory(model):
    open_model_dir(model)
    return ""


@app.route('/download_model/<model>')
def download_model(model):
    download_mod(model)
    return ""


@app.route('/delete_model/<model>')
def delete_model(model):
    remove_model(model)
    return render_template("pages/model_manager.html", models=read_downloaded_models(), only_content=True)


@app.route('/get_models')  # for transcription page
def get_models():
    models = read_downloaded_models()
    options = ''.join(
        [f'<option value="{model}">{model}</option>' for model in models])
    return options


# ----- Run App ------#
def run_app():
    app_height = int(min([monitor.height for monitor in get_monitors()])*0.8)
    app_width = int(min([monitor.width for monitor in get_monitors()])*0.8)
    window = webview.create_window(
        "aTrain", app, height=app_height, width=app_width)
    window.events.closed += teardown
    with keep.running():
        webview.start()


def cli():
    parser = argparse.ArgumentParser(
        prog='aTrain', description='A GUI tool to transcribe audio with Whisper')
    parser.add_argument("command", choices=[
                        'start', 'dev'], help="Command for aTrain to perform.")
    args = parser.parse_args()

    if args.command == "start":
        print("Running aTrain")
        run_app()

    if args.command == "dev":
        print("Running aTrain in dev mode")
        app.run()
