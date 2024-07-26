from .archive import read_archive, delete_transcription, open_file_directory, read_directories
from .models import open_model_dir, start_model_download, read_model_metadata, model_languages, stop_all_downloads
from .transcription import EVENT_SENDER, stop_all_transcriptions, start_process
from aTrain_core.load_resources import remove_model
from flask import Blueprint, render_template, redirect, Response, url_for, request

api = Blueprint("api", __name__)


@api.post("/start_transcription")
def start_transcription():
    start_process(request)
    return ""


@api.get("/stop_transcription")
def stop_transcription():
    stop_all_transcriptions()
    return redirect(url_for('routes.home'))


@api.get("/SSE")
def SSE():
    return Response(EVENT_SENDER.stream(), mimetype="text/event-stream")


@api.get('/open_directory/<file_id>')
def open_directory(file_id):
    open_file_directory(file_id)
    return ""


@api.get('/open_latest_transcription')
def open_latest_transcription():
    latest_transcription = read_directories()[0]
    open_file_directory(latest_transcription)
    return ""


@api.get("/delete_directory/<file_id>")
def delete_directory(file_id):
    delete_transcription(file_id)
    return render_template("routes/archive.html", archive_data=read_archive(), only_content=True)


@api.get('/open_model_directory/<model>')
def open_model_directory(model):
    open_model_dir(model)
    return ""


@api.get('/download_model/<model>')
def download_model(model):
    start_model_download(model)
    return render_template("routes/model_manager.html", models=read_model_metadata(), only_content=True)


@api.get('/stop_download')
def stop_download():
    stop_all_downloads()
    return ""


@api.get('/delete_model/<model>')
def delete_model(model):
    remove_model(model)
    return render_template("routes/model_manager.html", models=read_model_metadata(), only_content=True)


@api.get('/get_languages')  # for transcription page
def get_languages():
    model = request.form.get('model')
    # Use a different variable name to store the result
    languages_dict = model_languages(model)
    print(languages_dict)
    return render_template("settings/languages.html", languages=languages_dict)
