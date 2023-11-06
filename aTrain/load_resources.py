from importlib.resources import files
from huggingface_hub import snapshot_download
import shutil
import requests
import json
import os
from tqdm import tqdm
import platform

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
    model_path = str(files("aTrain.models").joinpath(model))
    if not os.path.exists(model_path):
        snapshot_download(repo_id=model_info["repo_id"], revision=model_info["revision"], local_dir=model_path, local_dir_use_symlinks=False)
    return model_path

def get_ffmpeg():
    system = platform.system()
    if system == "Windows":
        ffmpeg_path = get_ffmpeg_windows()
    if system in ["Darwin","Linux"]:
        ffmpeg_path ="ffmpeg"
    return ffmpeg_path

def get_ffmpeg_windows():
    ffmpeg_path = str(files("aTrain").joinpath("ffmpeg.exe"))
    if not os.path.exists(ffmpeg_path):
        url = 'https://github.com/GyanD/codexffmpeg/releases/download/6.0/ffmpeg-6.0-essentials_build.zip'
        ffmpeg_zip = str(files("aTrain").joinpath("ffmpeg.zip"))
        ffmpeg_dir = str(files("aTrain").joinpath("ffmpeg_dir"))
        ffmpeg_exe = os.path.join(ffmpeg_dir,"ffmpeg-6.0-essentials_build","bin","ffmpeg.exe")
        download_with_progress_bar(url,ffmpeg_zip)
        shutil.unpack_archive(ffmpeg_zip, ffmpeg_dir,"zip")  
        shutil.move(ffmpeg_exe,ffmpeg_path)    
        shutil.rmtree(ffmpeg_dir)
        os.remove(ffmpeg_zip)
    return ffmpeg_path

def download_with_progress_bar(url: str, filename: str, chunk_size=1024):
    resp = requests.get(url, stream=True)
    total = int(resp.headers.get('content-length', 0))
    with open(filename, 'wb') as file, tqdm(
        desc=filename,
        total=total,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in resp.iter_content(chunk_size=chunk_size):
            size = file.write(data)
            bar.update(size)

if __name__ == "__main__":
    ...