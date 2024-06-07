from pyannote.audio import Pipeline
from pyannote.core.utils.helper import get_class_by_name
from importlib.resources import files
import yaml
import os

class CustomPipeline(Pipeline):
    @classmethod
    def from_pretrained(cls,model_path) -> "Pipeline":
        config_yml = str(files("aTrain.models").joinpath("config.yaml"))
        with open(config_yml, "r") as config_file:
            config = yaml.load(config_file, Loader=yaml.SafeLoader)
        pipeline_name = config["pipeline"]["name"]
        Klass = get_class_by_name(pipeline_name, default_module_name="pyannote.pipeline.blocks")
        params = config["pipeline"].get("params", {})
        path_segmentation_model = os.path.join(model_path,"segmentation_pyannote.bin")
        path_embedding_model = os.path.join(model_path,"embedding_pyannote.bin")
        params["segmentation"] = path_segmentation_model.replace('\\', '/')
        params["embedding"] = path_embedding_model.replace('\\', '/')
        pipeline = Klass(**params)
        pipeline.instantiate(config["params"])
        return pipeline
