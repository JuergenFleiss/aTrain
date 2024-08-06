from .archive import read_archive, load_faqs
from .models import read_downloaded_models,  read_model_metadata, model_languages
from .settings import load_settings
from .version import __version__
from flask import Blueprint, render_template
from .globals import REQUIRED_MODELS

routes = Blueprint("routes", __name__)


@routes.context_processor
def set_globals():
    return dict(version=__version__)


@routes.get("/")
def home():
    default_model = read_downloaded_models()[0]
    languages = model_languages(default_model)
    return render_template("routes/transcribe.html", settings=load_settings(), models=read_downloaded_models(), languages=languages)


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
    return render_template("routes/model_manager.html", models=read_model_metadata(), REQUIRED_MODELS=REQUIRED_MODELS)
