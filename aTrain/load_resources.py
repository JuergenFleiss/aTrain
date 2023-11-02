from importlib.resources import files
from huggingface_hub import snapshot_download
import shutil
import requests
import json
import os

def download_all_resources():
    download_all_models()
    get_ffmpeg()

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

def get_ffmpeg():
    ffmpeg_path = str(files("aTrain").joinpath("ffmpeg.exe"))
    if not os.path.exists(ffmpeg_path):
        url = 'https://github.com/GyanD/codexffmpeg/releases/download/2023-10-02-git-9e531370b3/ffmpeg-2023-10-02-git-9e531370b3-essentials_build.zip'
        r = requests.get(url, allow_redirects=True)
        ffmpeg_zip = str(files("aTrain").joinpath("ffmpeg.zip"))
        ffmpeg_dir = str(files("aTrain").joinpath("ffmpeg"))
        ffmpeg_exe = os.path.join(ffmpeg_dir,"ffmpeg-2023-10-02-git-9e531370b3-essentials_build","bin","ffmpeg.exe")
        with open(ffmpeg_zip, 'wb') as ffmpeg_file:
            ffmpeg_file.write(r.content)
        shutil.unpack_archive(ffmpeg_zip, ffmpeg_dir,"zip")  
        shutil.move(ffmpeg_exe,ffmpeg_path)    
        shutil.rmtree(ffmpeg_dir)
        os.remove(ffmpeg_zip)
    return ffmpeg_path

if __name__ == "__main__":
    ...