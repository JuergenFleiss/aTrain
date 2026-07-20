import json
import shutil
from functools import partial
from importlib.resources import files
from multiprocessing.managers import DictProxy
from pathlib import Path

from huggingface_hub import file_download, snapshot_download
from tqdm.auto import tqdm

from aTrain_core.globals import MODELS_DIR, REQUIRED_MODELS, REQUIRED_MODELS_DIR


class custom_tqdm(tqdm):
    def __init__(self, progress: DictProxy, total: float, *args, **kwargs):
        self.progress = progress
        super().__init__(total=total, *args, **kwargs)

    def update(self, n=1):
        current = self.n + n
        self.progress["current"] = current
        super().update(n)


def download_all_models():
    """Downloads all models defined in the model configuration file."""
    models_config = load_model_config_file()
    for model in models_config:
        get_model(model)


def download_model(model_path: Path, model_info: dict, progress: DictProxy | None = None):
    if progress:
        # Monkey patching custom tqdm bar into the huggingface snapshot download
        repo_size = model_info["repo_size"]
        progress["total"] = repo_size
        tqdm_bar = custom_tqdm(total=repo_size, progress=progress)
        file_download.http_get = partial(file_download.http_get, _tqdm_bar=tqdm_bar)  # ty: ignore

    snapshot_download(
        repo_id=model_info["repo_id"],
        revision=model_info["revision"],
        local_dir=model_path,
        local_dir_use_symlinks=False,
        max_workers=1,
    )


def get_model(model: str, progress: DictProxy | None = None) -> Path:
    """Loads a specific model."""
    models_config = load_model_config_file()
    model_info = models_config[model]
    models_dir = REQUIRED_MODELS_DIR if model in REQUIRED_MODELS else MODELS_DIR
    model_path = models_dir / model
    if not model_path.exists():
        download_model(model_path, model_info, progress)
    return model_path


def remove_model(model: str, models_dir: Path = MODELS_DIR):
    model_path = models_dir / model
    if model_path.exists():
        shutil.rmtree(model_path)  # This deletes the directory and all its contents


def load_model_config_file() -> dict:
    """Loads the model configuration file."""
    models_config_path = str(files("aTrain_core.data").joinpath("models.json"))
    with open(models_config_path) as models_config_file:
        models_config: dict = json.load(models_config_file)
    return models_config


if __name__ == "__main__":
    ...
