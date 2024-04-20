from .output_files import create_output_files, named_tuple_to_dict, transform_speakers_results
from .archive import read_metadata, delete_transcription, add_processing_time_to_metadata, TRANSCRIPT_DIR
from .load_resources import get_model
import numpy as np
import os
import traceback
from flask import render_template
from .split_segs import split_audio
from pathlib import Path

def handle_transcription(file_id):
    try:
        filename, model, language, speaker_detection, num_speakers, device, compute_type = read_metadata(file_id)
        
        file_directory = os.path.join(TRANSCRIPT_DIR,file_id)
        prepared_file = os.path.join(file_directory, file_id + ".wav")
        log_metadata_to_file(filename=filename, model=model, language=language,
                        speaker_detection=speaker_detection, num_speakers=num_speakers,
                        device=device, compute_type=compute_type, prepared_file=prepared_file)
        segments = split_audio(prepared_file, file_directory, segment_duration=1800)  # Split the audio file into segments of 30 minutes each
        for segment in segments:
            name = Path(segment).name
            file_directory = os.path.join(TRANSCRIPT_DIR,name)
            prepared_file = os.path.join(file_directory, name + ".wav")
            for step in transcribe(segment, model, language, speaker_detection, num_speakers, device, compute_type):
                response = f"data: {step['task']}\n\n"
                yield response
            create_output_files(step["result"], speaker_detection, file_directory, filename)
            add_processing_time_to_metadata(name)
            os.remove(prepared_file)
            html = render_template("modals/modal_download.html", file_id=name).replace('\n', '')
            response = f"event: stopstream\ndata: {html}\n\n"
            yield response
    except Exception as e:
        delete_transcription(file_id)
        traceback_str = traceback.format_exc()
        error = str(e)
        html = render_template("modals/modal_error.html", error=error, traceback=traceback_str).replace('\n', '')
        response = f"event: stopstream\ndata: {html}\n\n"
        yield response
        
        
def log_metadata_to_file(**kwargs):
    log_file_path = 'C:\\Users\\dower\\Downloads\\transcribe_log.txt'
    with open(log_file_path, 'w') as f:
        for key, value in kwargs.items():
            try:
                f.write(f"{key}: {value}\n")
            except Exception as e:
                f.write(f"{key}: {e}\n")
    
    # Also print the logged information to console
    for key, value in kwargs.items():
        print(f"{key}: {value}")
    print()  # Just to add a newline at the end for better readability
    
def transcribe (audio_file, model, language, speaker_detection, num_speakers, device, compute_type):   
    import gc, torch #Import inside the function to speed up the startup time of the destkop app.
    from faster_whisper import WhisperModel
    from .pipeline import CustomPipeline
    
    language = None if language == "auto-detect" else language
    min_speakers = max_speakers = None if num_speakers == "auto-detect" else int(num_speakers)
    device = "cuda" if device=="GPU" else "cpu"

    yield {"task":"Loading whisper model"}
    model_path = get_model(model)
    transcription_model = WhisperModel(model_path,device,compute_type=compute_type)

    yield {"task":"Transcribing file with whisper"}
    transcription_segments, _ = transcription_model.transcribe(audio=audio_file,vad_filter=True, word_timestamps=True,language=language,no_speech_threshold=0.6)
    transcript = {"segments":[named_tuple_to_dict(segment) for segment in transcription_segments]}
    
    del transcription_model; gc.collect(); torch.cuda.empty_cache()
    
    if not speaker_detection:
        yield {"task":"Finishing up", "result" : transcript}
    
    if speaker_detection:
        yield {"task":"Loading speaker detection model"}
        model_path = get_model("diarize")
        diarize_model = CustomPipeline.from_pretrained(model_path).to(torch.device(device))
        yield {"task":"Detecting speakers"}
        diarization_segments = diarize_model(audio_file,min_speakers=min_speakers, max_speakers=max_speakers)
        speaker_results = transform_speakers_results(diarization_segments)
        del diarize_model; gc.collect(); torch.cuda.empty_cache()
        transcript_with_speaker = assign_word_speakers(speaker_results,transcript)
        yield {"task":"Finishing up", "result":transcript_with_speaker}

def assign_word_speakers(diarize_df, transcript_result, fill_nearest=False):
    #Function from whisperx -> see https://github.com/m-bain/whisperX.git
    transcript_segments = transcript_result["segments"]
    for seg in transcript_segments:
        diarize_df['intersection'] = np.minimum(diarize_df['end'], seg['end']) - np.maximum(diarize_df['start'], seg['start'])
        diarize_df['union'] = np.maximum(diarize_df['end'], seg['end']) - np.minimum(diarize_df['start'], seg['start'])
        dia_tmp = diarize_df[diarize_df['intersection'] > 0] if not fill_nearest else diarize_df
        if len(dia_tmp) > 0:
            speaker = dia_tmp.groupby("speaker")["intersection"].sum().sort_values(ascending=False).index[0]
            seg["speaker"] = speaker
        if 'words' in seg:
            for word in seg['words']:
                if 'start' in word:
                    diarize_df['intersection'] = np.minimum(diarize_df['end'], word['end']) - np.maximum(diarize_df['start'], word['start'])
                    diarize_df['union'] = np.maximum(diarize_df['end'], word['end']) - np.minimum(diarize_df['start'], word['start'])
                    dia_tmp = diarize_df[diarize_df['intersection'] > 0] if not fill_nearest else diarize_df
                    if len(dia_tmp) > 0:
                        speaker = dia_tmp.groupby("speaker")["intersection"].sum().sort_values(ascending=False).index[0]
                        word["speaker"] = speaker
    return transcript_result    

if __name__ == "__main__":
    ...
    
