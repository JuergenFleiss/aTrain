from .utils import read_archive, delete_transcription, open_file_directory, load_faqs
from .version import __version__
from .settings import load_settings
from .process import EVENT_SENDER, RUNNING_PROCESSES, kill_all_processes
from .mockup_core import transcribe
from flask import Flask, render_template, request, redirect, Response
from screeninfo import get_monitors
from multiprocessing import Process
import webview
from wakepy import keep
import time
import argparse

#-----Setup------#
app = Flask(__name__)

@app.template_filter
def format_duration(duration): 
    return time.strftime("%Hh %Mm %Ss", time.gmtime(duration))

@app.context_processor
def set_globals():
    return dict(version=__version__)

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
    transciption = Process(target=transcribe, kwargs={"event_sender" : EVENT_SENDER}, daemon=True)
    transciption.start()
    RUNNING_PROCESSES.append(transciption)
    return ""

@app.route("/stop_transcription")
def stop_transcription():
    kill_all_processes()
    return redirect(request.referrer)

@app.get("/SSE")
def SSE():
    return Response(EVENT_SENDER.stream(), mimetype="text/event-stream")

@app.route('/open/<file_id>')
def open_directory(file_id):
    open_file_directory(file_id)
    return ""
    
@app.route("/delete/<file_id>")
def delete_directory(file_id):
    delete_transcription(file_id)
    archive_data = read_archive()
    return render_template("pages/archive.html", archive_data=archive_data, only_content=True)

#-----Run App------#
def run_app():
    app_height = int(min([monitor.height for monitor in get_monitors()])*0.8)
    app_width = int(min([monitor.width for monitor in get_monitors()])*0.8)

    window = webview.create_window("aTrain",app,height=app_height,width=app_width)
    window.events.closed += EVENT_SENDER.stop
    with keep.running():
        webview.start()

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