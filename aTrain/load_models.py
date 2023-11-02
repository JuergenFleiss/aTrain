from importlib.resources import files
from huggingface_hub import snapshot_download
import json
import os

def download_all_models():
    models_config = load_model_config_file()
    for model in models_config:
        get_model(model)

def load_model_config_file():
    models_config_path = str(files("aTrain.models").joinpath("models.json"))
    with open(models_config_path, "r") as models_config_file:
        models_config = json.load(models_config_file)
    return models_config

def get_model(model):
    models_config = load_model_config_file()
    model_info = models_config[model]
    model_path = str(files("aTrain.models").joinpath(os.path.join(*model_info["path"])))
    if not os.path.exists(model_path):
        snapshot_download(repo_id=model_info["repo_id"],revision=model_info["revision"],cache_dir=str(files("aTrain.models").joinpath("")))
    return model_path

if __name__ == "__main__":
    ...