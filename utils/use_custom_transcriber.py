import json
import os
import pandas as pd
from huggingface_hub import snapshot_download
from utils.output_files import create_json_file

def use_transcriber (file_directory, audio_file, model, language, speaker_detection, num_speakers):   
    import gc, torch #Import inside the function to speed up the startup time of the destkop app.
    from faster_whisper import WhisperModel
    from pyannote.audio import Pipeline
    from whisperx import load_audio, assign_word_speakers

    language = None if language == "auto-detect" else language
    min_speakers = max_speakers = None if num_speakers == "auto-detect" else int(num_speakers)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"
    
    yield {"task":"Loading whisper model"}
    model_path = get_model(model)
    transcription_model = WhisperModel(model_path,device,compute_type=compute_type)

    yield {"task":"Transcribing file with whisper"}
    audio_array = load_audio(audio_file)
    transcription_segments, _ = transcription_model.transcribe(audio=audio_array,vad_filter=True, word_timestamps=True,language=language,no_speech_threshold=0.6)
    transcript = {"segments":[named_tuple_to_dict(segment) for segment in transcription_segments]}
    
    del transcription_model; gc.collect(); torch.cuda.empty_cache()
    
    if not speaker_detection:
        create_json_file(file_directory,outfile_name="transcription.json",content=transcript)
        yield {"task":"Finishing up", "result" : transcript}
    
    if speaker_detection:
        yield {"task":"Loading speaker detection model"}
        get_model("diarize")
        pipeline_config = os.path.join("models","config.yaml")
        diarize_model = Pipeline.from_pretrained(pipeline_config, cache_dir="models").to(device)
        
        yield {"task":"Detecting speakers"}
        diarization_segments = diarize_model(audio_file,min_speakers=min_speakers, max_speakers=max_speakers)
        speaker_results = transform_speakers_results(diarization_segments)
        del diarize_model; gc.collect(); torch.cuda.empty_cache()
        transcript_with_speaker = assign_word_speakers(speaker_results,transcript)
        create_json_file(file_directory,outfile_name="transcription.json",content=transcript_with_speaker)
        
        yield {"task":"Finishing up", "result":transcript_with_speaker}

def get_model(model):
    models_config_path = os.path.join("models","models.json")
    with open(models_config_path, "r") as models_config_file:
        models_config = json.load(models_config_file)
    model_info = models_config[model]
    model_path = os.path.join(*model_info["path"])
    if not os.path.exists(model_path):
        snapshot_download(repo_id=model_info["repo_id"],revision=model_info["revision"],cache_dir="models")
    return model_path

def transform_speakers_results(diarization_segments):    
    diarize_df = pd.DataFrame(diarization_segments.itertracks(yield_label=True))
    diarize_df['start'] = diarize_df[0].apply(lambda x: x.start)
    diarize_df['end'] = diarize_df[0].apply(lambda x: x.end)
    diarize_df.rename(columns={2: "speaker"}, inplace=True)
    return diarize_df

def named_tuple_to_dict(obj):
    if isinstance(obj, dict):
        return {key: named_tuple_to_dict(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [named_tuple_to_dict(value) for value in obj]
    elif isnamedtupleinstance(obj):
        return {key: named_tuple_to_dict(value) for key, value in obj._asdict().items()}
    elif isinstance(obj, tuple):
        return tuple(named_tuple_to_dict(value) for value in obj)
    else:
        return obj

def isnamedtupleinstance(x):
    _type = type(x)
    bases = _type.__bases__
    if len(bases) != 1 or bases[0] != tuple:
        return False
    fields = getattr(_type, '_fields', None)
    if not isinstance(fields, tuple):
        return False
    return all(type(i)==str for i in fields)

if __name__ == "__main__":
    ...