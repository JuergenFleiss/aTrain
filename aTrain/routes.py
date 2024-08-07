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


# @routes.get("/")
# def home():
#     models = read_downloaded_models()
#     default_model = "large-v3" if "large-v3" in models else None  # Set to None if "large-v3" is not available
#     languages = model_languages(default_model) if default_model else {}  # Use an empty dict if no default model
#     return render_template(
#         "routes/transcribe.html", 
#         settings=load_settings(), 
#         models=models, 
#         languages=languages, 
#         default_model=default_model
#     )

@routes.get("/")
def home():
    models = read_downloaded_models()  # Get the list of downloaded models
    
    try:
        if "large-v3" in models:
            default_model = "large-v3"
        elif models:
            default_model = models[0]  # Fall back to the first model if any models are available
        
        languages = model_languages(default_model)
        print("There appear to be no models downloaded")
        return render_template(
        "routes/transcribe.html", 
        settings=load_settings(), 
        models=models, 
        languages=languages, 
        default_model=default_model  # Pass the default model to the template
    )
    
    except KeyError:
        default_model = None  # No models available
        languages = {}
        return render_template(
        "routes/transcribe.html", 
        settings=load_settings(), 
        models=models, 
        languages=languages, 
        default_model=default_model  # Pass the default model to the template
    )
    
    
    

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
