import os
import json 
import pandas as pd
import time

def create_output_files(result, speaker_detection, file_directory, orig_filename):
        create_json_file(result, file_directory)
        create_txt_file(result, file_directory, orig_filename, speaker_detection, maxqda=False, timestamps = False)
        create_txt_file(result, file_directory, orig_filename, speaker_detection, maxqda=False, timestamps = True)
        create_txt_file(result, file_directory, orig_filename, speaker_detection, maxqda=True, timestamps = True)
        create_srt_file(result, file_directory)

def create_json_file(result, file_directory):
        output_file_text = os.path.join(file_directory,"transcription.json")
        with open(output_file_text,"w", encoding="utf-8") as json_file:
            json.dump(result, json_file,ensure_ascii=False)

def create_txt_file (result,file_directory, orig_filename, speaker_detection, timestamps, maxqda):
    segments = result["segments"]
    match maxqda, timestamps:
         case True, _ :  filename = "transcription_maxqda.txt"
         case False, True: filename = "transcription_timestamps.txt"
         case False, False: filename = "transcription.txt"
    file_path = os.path.join(file_directory, filename)
    with open(file_path, "w",encoding="utf-8") as file:
        headline = f"Transcription for {orig_filename}" + ( "" if maxqda and speaker_detection else "\n") + ("" if speaker_detection else "\n" )
        file.write(headline)
        current_speaker = None
        for segment in segments:
            speaker = segment["speaker"] if "speaker" in segment else "Speaker undefined"
            if speaker != current_speaker and speaker_detection:
                file.write(("\n\n" if maxqda else "\n") + speaker + "\n")
                current_speaker = speaker
            text = str(segment["text"]).lstrip()
            if timestamps:
                start_time = time.strftime("[%H:%M:%S]", time.gmtime(segment["start"]))
                text = f"{start_time} - {text}"
            file.write(text + (" " if maxqda else  "\n"))

def create_srt_file(result,file_directory):
    segments = result["segments"]
    file_path = os.path.join(file_directory, "transcription.srt")
    with open(file_path,"w", encoding="utf-8") as srt_file:
        for index, segment in enumerate(segments,1):
            srt_file.write(f"{index}\n")
            start_time = segment["start"]
            end_time = segment["end"]
            start_time_format = time.strftime("%H:%M:%S", time.gmtime(start_time)) + f",{round((start_time-int(start_time))*1000):03}"
            end_time_format = time.strftime("%H:%M:%S", time.gmtime(end_time)) + f",{round((end_time-int(end_time))*1000):03}"
            srt_file.write(f"{start_time_format} --> {end_time_format}\n")
            srt_file.write(f"{str(segment['text']).lstrip()}\n\n")

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