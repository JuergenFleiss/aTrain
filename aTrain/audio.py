from .load_resources import get_ffmpeg
from .custom_ffmpeg import run
import os
import ffmpeg
from scipy.io import wavfile
import numpy as np
import time

def prepare_audio (file_id,file_path,file_directory):
    ffmpeg_path = get_ffmpeg() #download ffmpeg if it does not exist
    output_file = file_id + ".wav"
    output_path =  os.path.join(file_directory,output_file)
    stream = ffmpeg.input(file_path)
    stream = ffmpeg.output(stream, output_path)
    run(stream,quiet=True, cmd=ffmpeg_path)
    return output_path

def get_audio_duration(file_path):
    sample_rate, data = wavfile.read(file_path)
    len_data = len(data)
    duration = int(len_data / sample_rate)
    return duration

def format_duration(duration): 
    return time.strftime("%Hh %Mm %Ss", time.gmtime(duration))

def load_audio(file: str, sr: int = 16000):
    ffmpeg_path = get_ffmpeg()
    try:
        stream = ffmpeg.input(file, threads=0)
        stream = ffmpeg.output(stream,"-", format="s16le", acodec="pcm_s16le", ac=1, ar=sr)
        out, _ = run(stream,cmd=[str(ffmpeg_path), "-nostdin"], capture_stdout=True, capture_stderr=True) 
    except ffmpeg.Error as e:
        raise RuntimeError(f"Failed to load audio: {e.stderr.decode()}") from e
    return np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0