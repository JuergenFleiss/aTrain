from .archive import read_archive, delete_transcription, open_file_directory
from .version import __version__
from .settings import load_settings
from flask import Flask, render_template, request, redirect
from importlib.resources import files
from screeninfo import get_monitors
import webview
from wakepy import keep
import traceback
import yaml
import time
import argparse

#-----Setup------#
app = Flask(__name__)

@app.template_filter
def format_duration(duration): 
    return time.strftime("%Hh %Mm %Ss", time.gmtime(duration))

@app.context_processor
def set_globals():
    return dict(version=__version__, settings=load_settings())

#-----Routes------#

@app.get("/")
def home():
    return render_template("pages/transcribe.html")

@app.get("/archive")
def archive():
    archive_data = read_archive()
    return render_template("pages/archive.html", archive_data=archive_data)

@app.get("/faq")
def faq():
    faq_path = str(files("aTrain.faq").joinpath("faq.yaml"))
    with open(faq_path,"r", encoding='utf-8') as faq_file:
        faqs = yaml.safe_load(faq_file)
    return render_template("pages/faq.html", faqs = faqs)

@app.post("/transcribe")
def transcribe():
    
    return render_template("modals/modal_wrongInput.html")

    #return render_template("modals/modal_process.html", id=file_id, task="Processing file", total_duration=estimated_process_time, device=device)

    #except Exception as error:
    #    delete_transcription(timestamp)
    #    traceback_str = traceback.format_exc()
    #    error = str(error)
    #    return render_template("modals/modal_error.html",error=error, traceback=traceback_str)

@app.route('/open/<file_id>')
def open_directory(file_id):
    open_file_directory(file_id)
    return ""
    
@app.route("/delete/<file_id>")
def delete_directory(file_id):
    delete_transcription(file_id)
    archive_data = read_archive()
    return render_template("pages/archive.html", archive_data=archive_data)

@app.route("/revert_changes/<upload_id>")
def revert_changes(upload_id):
    delete_transcription(upload_id)
    return redirect(request.referrer)

def run_app():
    app_height = int(min([monitor.height for monitor in get_monitors()])*0.8)
    app_width = int(min([monitor.width for monitor in get_monitors()])*0.8)
    webview.create_window("aTrain",app,height=app_height,width=app_width)
    with keep.running():
        webview.start()

def cli():
    parser = argparse.ArgumentParser(prog='aTrain', description='A GUI tool to transcribe audio with Whisper')
    parser.add_argument("command", choices=['start'], help="Command for aTrain to perform.")
    args = parser.parse_args()

    if args.command == "start":
        print("Running aTrain")
        run_app()