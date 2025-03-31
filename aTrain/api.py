from aTrain_core.load_resources import remove_model
from flask import Blueprint, Response, redirect, render_template, request, url_for

from .archive import (
    delete_transcription,
    open_file_directory,
    read_archive,
    read_directories,
)
from aTrain_core.globals import MODELS_DIR, REQUIRED_MODELS, REQUIRED_MODELS_DIR
from .models import (
    model_languages,
    read_model_metadata,
    start_model_download,
    stop_all_downloads,
)
from .transcription import EVENT_SENDER, start_process, stop_all_transcriptions

api = Blueprint("api", __name__)


@api.post("/start_transcription")
def start_transcription():
    start_process(request)
    return ""


@api.get("/stop_transcription")
def stop_transcription():
    stop_all_transcriptions()
    return redirect(url_for("routes.home"))


@api.get("/SSE")
def SSE():
    return Response(EVENT_SENDER.stream(), mimetype="text/event-stream")


@api.get("/open_directory/<file_id>")
def open_directory(file_id):
    open_file_directory(file_id)
    return ""


@api.get("/open_latest_transcription")
def open_latest_transcription():
    latest_transcription = read_directories()[0]
    open_file_directory(latest_transcription)
    return ""


@api.get("/delete_directory/<file_id>")
def delete_directory(file_id):
    delete_transcription(file_id)
    return render_template(
        "routes/archive.html", archive_data=read_archive(), only_content=True
    )


@api.get("/download_model/<model>")
def download_model(model):
    if model in REQUIRED_MODELS:
        models_dir = REQUIRED_MODELS_DIR
    else:
        models_dir = MODELS_DIR
    start_model_download(model, models_dir)
    return render_template(
        "routes/model_manager.html",
        models=read_model_metadata(),
        only_content=True,
        REQUIRED_MODELS=REQUIRED_MODELS,
    )


@api.get("/stop_download")
def stop_download():
    stop_all_downloads()
    return ""


@api.get("/delete_model/<model>")
def delete_model(model):
    remove_model(model)
    return render_template(
        "routes/model_manager.html",
        models=read_model_metadata(),
        only_content=True,
        REQUIRED_MODELS=REQUIRED_MODELS,
    )
