# transcribe.py class-based methods

from .output_files import create_output_files, named_tuple_to_dict, transform_speakers_results
from .archive import read_metadata, delete_transcription, add_processing_time_to_metadata, TRANSCRIPT_DIR
from .load_resources import get_model
import numpy as np
import os
import traceback
from flask import render_template
from .segment_audio import split_audio
from pathlib import Path
import json

class TranscriptSegment:
    def __init__(self, segment_path, file_directory, model, language, speaker_detection, 
                        num_speakers, device, compute_type, file_id, log_file_path, 
                        filename, segment_index):
        self.segment_path = segment_path
        self.file_directory = file_directory
        self.model = model
        self.language = language
        self.speaker_detection = speaker_detection
        self.num_speakers = num_speakers
        self.device = device
        self.compute_type = compute_type
        self.file_id = file_id
        self.log_file_path = log_file_path
        self.filename = filename
        self.segment_index = segment_index

    def process_segment(self):
        """
        Transcribes a single segment, logs metadata, and updates transcripts.
        """
        try:
            name = Path(self.segment_path).stem
            prepared_file = os.path.join(self.file_directory, name + ".wav")
            print(f'Transcribing segment: {name}')
            transcription_handler = TranscriptionHandler(self.file_id)  # Assuming TranscriptionHandler has helper methods
            for step in transcription_handler.transcribe(self.segment_path, self.model, 
                                                            self.language, self.speaker_detection, self.num_speakers, 
                                                            self.device, self.compute_type):
                yield {"task": step["task"]}
            
            transcription_handler.log_metadata_to_file(speaker=self.speaker_detection, 
                                                        file_id=name, prepared_file=prepared_file, filename=self.filename)
            
            transcript_result = step.get("result") if step and "result" in step else {}
            
            transcript_update = create_output_files(transcript_result, self.speaker_detection, 
                                                        self.file_directory, self.filename, self.segment_index)
            
            try:
                add_processing_time_to_metadata(name)
                os.remove(prepared_file)
            except Exception as e:
                print(f"Error removing file {prepared_file}: {str(e)}")
            return transcript_update
        except Exception as e:
            print(f"Error processing segment {self.segment_path}: {str(e)}")
            return {}

# Adjust TranscriptionHandler to use TranscriptSegment
class TranscriptionHandler:
    def __init__(self, file_id, log_file_path):
        self.file_id = file_id
        self.log_file_path = log_file_path
        self.transcripts_path = "C:\\Users\\dower\\Documents\\transcripts.json"
        
    def handle_transcription(self):
        try:
            metadata = read_metadata(self.file_id)
            file_directory = os.path.join(TRANSCRIPT_DIR, self.file_id)

            segments = split_audio(os.path.join(file_directory, self.file_id + ".wav"), file_directory, segment_duration=1500)
            
            transcripts = {}
            for k, segment in enumerate(segments):
                segment_processor = TranscriptSegment(segment, file_directory, *metadata, self.file_id, self.log_file_path, metadata.filename, k)
                for step in segment_processor.process_segment():
                    yield f"data: {step['task']}\n\n"
                transcripts.update(step)
            
            # Once all segments are processed, compile and save the complete transcript
            with open(self.transcripts_path, 'w') as f:
                json.dump(transcripts, f)

            html = render_template("modals/modal_download.html", file_id=self.file_id).replace('\n', '')
            yield f"event: stopstream\ndata: {html}\n\n"
        except Exception as e:
            traceback_str = traceback.format_exc()
            error = str(e)
            html = render_template("modals/modal_error.html", error=error, traceback=traceback_str).replace('\n', '')
            yield f"event: stopstream\ndata: {html}\n\n"
            
    def log_metadata_to_file(self, **kwargs):
        with open(self.log_file_path, 'a') as f:
            for key, value in kwargs.items():
                try:
                    f.write(f"\n\n{key}: {value}\n")
                except Exception as e:
                    f.write(f"{key}: {e}\n")
        
        # Also print the logged information to console
        for key, value in kwargs.items():
            print(f"{key}: {value}")
        print()  # Just to add a newline at the end for better readability
        
    def transcribe (self, audio_file, model, language, speaker_detection, num_speakers, device, compute_type):   
        import gc, torch
        from faster_whisper import WhisperModel
        from .pipeline import CustomPipeline
        
        language = None if language == "auto-detect" else language
        min_speakers = max_speakers = None if num_speakers == "auto-detect" else int(num_speakers)
        device = "cuda" if device=="GPU" else "cpu"

        yield {"task":"Loading whisper model"}
        model_path = get_model(model)
        transcription_model = WhisperModel(model_path, device, compute_type=compute_type)

        yield {"task":"Transcribing file with whisper"}
        transcription_segments, _ = transcription_model.transcribe(audio=audio_file, vad_filter=True, 
                                                                word_timestamps=True, language=language, no_speech_threshold=0.6)
        transcript ={"segments": [named_tuple_to_dict(segment) for segment in transcription_segments]}

        del transcription_model; gc.collect(); torch.cuda.empty_cache()

        if not speaker_detection:
            yield {"task": "Finishing up", "result": transcript}

        if speaker_detection:
            yield {"task": "Loading speaker detection model"}
            model_path = get_model("diarize")
            diarize_model = CustomPipeline.from_pretrained(model_path).to(torch.device(device))
            yield {"task": "Detecting speakers"}
            diarization_segments = diarize_model(audio_file, min_speakers=min_speakers, max_speakers=max_speakers)
            speaker_results = transform_speakers_results(diarization_segments)
            del diarize_model; gc.collect(); torch.cuda.empty_cache()
            transcript_with_speaker = self.assign_word_speakers(speaker_results, transcript)
            yield {"task": "Finishing up", "result": transcript_with_speaker}

    def assign_word_speakers(self, diarize_df, transcript_result, fill_nearest=False):
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
                    diarize_df['intersection'] = np.minimum(diarize_df['end'], word['end']) - np.maximum(diarize_df['start'], word['start'])
                    diarize_df['union'] = np.maximum(diarize_df['end'], word['end']) - np.minimum(diarize_df['start'], word['start'])
                    dia_tmp = diarize_df[diarize_df['intersection'] > 0] if not fill_nearest else diarize_df
                    if len(dia_tmp > 0):
                        speaker = dia_tmp.groupby("speaker")["intersection"].sum().sort_values(ascending=False).index[0]
                        word["speaker"] = speaker
        return transcript_result
