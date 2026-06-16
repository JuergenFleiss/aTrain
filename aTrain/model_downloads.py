from aTrain_core.globals import MODELS_DIR, REQUIRED_MODELS, REQUIRED_MODELS_DIR
from aTrain_core.load_resources import load_model_config_file


def check_model_downloaded(model: str) -> None:
    available_models = load_model_config_file()
    if model not in available_models:
        raise ValueError(f"Model {model} is not available.")

    models_dir = REQUIRED_MODELS_DIR if model in REQUIRED_MODELS else MODELS_DIR
    model_path = models_dir / model
    if not model_path.exists() or not any(model_path.rglob("*.bin")):
        raise FileNotFoundError(
            f"Model {model} is not downloaded. Download it from the Models page or run: aTrain init"
        )
