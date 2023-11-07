from .transcribe import handle_transcription
from .handle_upload import check_inputs, get_inputs, handle_file
from .archive import read_archive, create_metadata, delete_transcription, open_file_directory, TIMESTAMP_FORMAT
from .load_resources import download_all_resources
from .version import VERSION
from .custom_flaskwebgui import CustomUI
from flask import Flask, render_template, request, redirect, stream_with_context
from importlib.resources import files
from screeninfo import get_monitors
import webview
from wakepy import keep
import traceback
import yaml
import time
from datetime import datetime
import webbrowser
import argparse

app = Flask(__name__)

def format_duration(duration): 
    return time.strftime("%Hh %Mm %Ss", time.gmtime(duration))
app.jinja_env.filters['format_duration'] = format_duration

@app.get("/")
def render_home():
    return render_template("index.html", version=VERSION)

@app.get("/transcribe")
def render_transcribe():
    return render_template("pages/transcribe.html")

@app.get("/archive")
def render_archive():
    archive_data = read_archive()
    return render_template("pages/archive.html", archive_data=archive_data)

@app.get("/faq")
def render_faq():
    faq_path = str(files("aTrain.faq").joinpath("faq.yaml"))
    with open(faq_path,"r", encoding='utf-8') as faq_file:
        faqs = yaml.safe_load(faq_file)
    return render_template("pages/faq.html", faqs = faqs)

@app.get("/settings")
def get_default_settings():
    from torch.cuda import is_available as cuda_available
    return render_template("modals/modal_settings.html", cuda_available=cuda_available())

@app.post("/upload")
def upload():
    timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
    try:
        file, model, language, speaker_detection, num_speakers, device, compute_type = get_inputs(request) 
        inputs_correct = check_inputs(file, model, language, num_speakers)
        if inputs_correct is False:
            return render_template("modals/modal_wrongInput.html")
        filename, file_id, estimated_process_time, audio_duration = handle_file(file, timestamp, model, device)
        create_metadata(file_id, filename, audio_duration, model, language, speaker_detection, num_speakers, device, compute_type, timestamp)
        return render_template("modals/modal_process.html", id=file_id, task="Processing file", total_duration=estimated_process_time, device=device)
    except Exception as error:
        delete_transcription(timestamp)
        traceback_str = traceback.format_exc()
        error = str(error)
        return render_template("modals/modal_error.html",error=error, traceback=traceback_str)

@app.route("/transcription/<upload_id>")
def stream_data(upload_id):
    return stream_with_context(handle_transcription(upload_id)), {"Content-Type": "text/event-stream"}

@app.route('/open/<file_id>')
def open_transcription(file_id):
    open_file_directory(file_id)
    return ""
    
@app.route("/delete/<file_id>")
def delete_archive_files(file_id):
    delete_transcription(file_id)
    archive_data = read_archive()
    return render_template("pages/archive.html", archive_data=archive_data)

@app.route("/revert_changes/<upload_id>")
def revert_latest_changes(upload_id):
    delete_transcription(upload_id)
    return redirect(request.referrer)

@app.get("/openbrowser/<website>")
def open_browser(website):
    match website:
        case "github": url = "https://github.com/BANDAS-Center/aTrain"
        case "feedback": url = "https://survey.uni-graz.at/index.php/381219"
    webbrowser.open_new(url)
    return ""

def run_app():
    app_height = int(min([monitor.height for monitor in get_monitors()])*0.8)
    app_width = int(min([monitor.width for monitor in get_monitors()])*0.8)
    try:
        webview.create_window("aTrain",app,height=app_height,width=app_width)
        with keep.running():
            webview.start()
    except:
        try:
            browser_options = ["--bwsi","--disable-features=Translate"]
            with keep.running():
                CustomUI(app=app, server="flask", fullscreen=True, custom_flags=browser_options).run()
        except:
            with keep.running():
                CustomUI(app=app, server="flask", fullscreen=True).run()

def cli():
    parser = argparse.ArgumentParser(prog='aTrain', description='A GUI tool to transcribe audio with Whisper')
    parser.add_argument("command", choices=['init', 'start'], help="Command for aTrain to perform.")
    args = parser.parse_args()

    if args.command == "init":
        print("Downloading all models:")
        download_all_resources()
        print("Finished")
    if args.command == "start":
        print("Running aTrain")
        run_app()