from .utils import read_archive, delete_transcription, open_file_directory, load_faqs
from .version import __version__
from .settings import load_settings
from .SSE import stream_events, send_event, stop_SSE
from .globals import SERVER_EVENTS
from .mockup_core import check_inputs, transcribe
from flask import Flask, render_template, request, redirect, Response
from screeninfo import get_monitors
from threading import Thread
import webview
from wakepy import keep
import json
import traceback
import time
import argparse

#-----Setup------#
app = Flask(__name__)

@app.template_filter
def format_duration(duration): 
    return time.strftime("%Hh %Mm %Ss", time.gmtime(duration))

@app.context_processor
def set_globals():
    return dict(version=__version__, server_events=SERVER_EVENTS)

#-----Routes------#

@app.get("/")
def home():
    return render_template("pages/transcribe.html", settings=load_settings())

@app.get("/archive")
def archive():
    return render_template("pages/archive.html", archive_data=read_archive())

@app.get("/faq")
def faq():
    return render_template("pages/faq.html", faqs = load_faqs())

@app.post("/start_transcription")
def start_transcription():
    input_correct = check_inputs()

    if not input_correct:
        send_event("",event=SERVER_EVENTS.wrong_input)
        return ""
    try:
        t = Thread(target=transcribe, daemon=True)
        t.start()
        return ""
        
    except Exception as error:
        traceback_str = traceback.format_exc()
        error = str(error)
        error_data = json.dumps({"error" : error, "traceback" : traceback_str})
        send_event(error_data, event=SERVER_EVENTS.error)
        return ""

@app.route("/stop_transcription")
def stop_transcription():
    return redirect(request.referrer)

@app.get("/SSE")
def SSE():
    return Response(stream_events(), mimetype="text/event-stream")

@app.route('/open/<file_id>')
def open_directory(file_id):
    open_file_directory(file_id)
    return ""
    
@app.route("/delete/<file_id>")
def delete_directory(file_id):
    delete_transcription(file_id)
    archive_data = read_archive()
    return render_template("pages/archive.html", archive_data=archive_data)

#-----Run App------#
def run_app():
    app_height = int(min([monitor.height for monitor in get_monitors()])*0.8)
    app_width = int(min([monitor.width for monitor in get_monitors()])*0.8)

    global window
    window = webview.create_window("aTrain",app,height=app_height,width=app_width)
    window.expose(file_dialog)
    window.events.closed += stop_SSE

    with keep.running():
        webview.start()

def file_dialog():
        file_types = ('Audio Files (*.mp3;*.wav)', 'Video Files (*.mp4)')
        result = window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
        return(result)

def cli():
    parser = argparse.ArgumentParser(prog='aTrain', description='A GUI tool to transcribe audio with Whisper')
    parser.add_argument("command", choices=['start', 'dev'], help="Command for aTrain to perform.")
    args = parser.parse_args()

    if args.command == "start":
        print("Running aTrain")
        run_app()

    if args.command == "dev":
        print("Running aTrain in dev mode")
        app.run()