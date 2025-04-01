from aTrain_core.globals import DOCUMENTS_DIR, REQUIRED_MODELS
from flask import Blueprint, render_template, request
from torch import cuda

from .archive import load_faqs, read_archive, check_access
from .models import model_languages, read_downloaded_models, read_model_metadata
from .version import __version__

routes = Blueprint("routes", __name__)


@routes.context_processor
def set_globals():
    return dict(version=__version__)


@routes.get("/")
def home():
    if check_access(DOCUMENTS_DIR):
        models = read_downloaded_models()  # Get the list of downloaded models

        try:
            if REQUIRED_MODELS[1] in models:
                default_model = REQUIRED_MODELS[1]
            elif models:
                default_model = models[
                    0
                ]  # Fall back to the first model if any models are available

            languages = model_languages(default_model)
            return render_template(
                "routes/transcribe.html",
                cuda=cuda.is_available(),
                models=models,
                languages=languages,
                default_model=default_model,  # Pass the default model to the template
            )

        except KeyError:
            default_model = None  # No models available
            languages = {}
            return render_template(
                "routes/transcribe.html",
                cuda=cuda.is_available(),
                models=models,
                languages=languages,
                default_model=default_model,  # Pass the default model to the template
            )
    else:
        return render_template("routes/transcribe.html") ##changed from access_required.html for snap debugging


@routes.get("/archive")
def archive():
    return render_template("routes/archive.html", archive_data=read_archive())


@routes.get("/faq")
def faq():
    return render_template("routes/faq.html", faqs=load_faqs())


@routes.get("/about")
def about():
    return render_template("routes/about.html")


@routes.get("/model_manager")
def model_manager():
    return render_template(
        "routes/model_manager.html",
        models=read_model_metadata(),
        REQUIRED_MODELS=REQUIRED_MODELS,
    )


@routes.route("/get_languages", methods=["GET", "POST"])
def get_languages():
    model = request.form.get("model")
    languages_dict = model_languages(model)
    return render_template("settings/languages.html", languages=languages_dict)
