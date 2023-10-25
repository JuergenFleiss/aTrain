from flask import Flask, render_template, request, redirect, stream_with_context
from utils.transcribe import handle_transcription
from utils.handle_upload import check_inputs, get_inputs, handle_file, format_duration
from utils.archive import read_archive, create_metadata, delete_transcription, open_file_directory, TIMESTAMP_FORMAT
import traceback
import webview
from screeninfo import get_monitors
import yaml
from datetime import datetime
from wakepy import keep
import webbrowser
from version import VERSION

app = Flask(__name__)
app.jinja_env.filters['format_duration'] = format_duration

@app.get("/")
def render_home():
    return render_template("index.html", version=VERSION)

@app.get("/transcribe")
def render_transcribe():
    return render_template("transcribe.html")

@app.get("/archive")
def render_archive():
    archive_data = read_archive()
    return render_template("archive.html", archive_data=archive_data)

@app.get("/faq")
def render_faq():
    faq_path = "faq.yaml"
    with open(faq_path,"r", encoding='utf-8') as faq_file:
        faqs = yaml.safe_load(faq_file)
    return render_template("faq.html", faqs = faqs)

@app.post("/upload")
def upload():
    timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
    try:
        file, model, language, speaker_detection, num_speakers = get_inputs(request) 
        inputs_correct = check_inputs(file, model, language, num_speakers)
        if inputs_correct is False:
            return render_template("modal_wrongInput.html")
        filename, file_id, estimated_process_time, device, audio_duration = handle_file(file, timestamp, model)
        create_metadata(file_id, filename, audio_duration, model, language, speaker_detection, num_speakers, device, timestamp)
        return render_template("modal_process.html", id=file_id, task="Processing file", total_duration=estimated_process_time, device=device)
    except Exception as error:
        delete_transcription(timestamp)
        traceback_str = traceback.format_exc()
        error = str(error)
        return render_template("modal_error.html",error=error, traceback=traceback_str)

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
    return render_template("archive.html", archive_data=archive_data)

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

def get_screen_size():
    scaler = 0.8
    height = min([monitor.height for monitor in get_monitors()])*scaler
    width = min([monitor.width for monitor in get_monitors()])*scaler
    return round(width), round(height)

if __name__ == "__main__":
    #app.run(port=5000)
    width, height = get_screen_size()
    webview.create_window("aTrain",app, height=height, width=width)
    with keep.running() as k:
        webview.start()