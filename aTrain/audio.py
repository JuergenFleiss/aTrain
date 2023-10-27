import os
import ffmpeg
import requests
import shutil
from scipy.io import wavfile
from archive import APP_DIR

def prepare_audio (file_id,file_path,file_directory):
    ffmpeg_path = get_ffmpeg() #download ffmpeg if it does not exist
    output_file = file_id + ".wav"
    output_path =  os.path.join(file_directory,output_file)
    stream = ffmpeg.input(file_path)
    stream = ffmpeg.output(stream, output_path)
    ffmpeg.run(stream,quiet=True, cmd=ffmpeg_path)
    return output_path

def get_ffmpeg():
    ffmpeg_path = os.path.join(APP_DIR,"ffmpeg.exe")
    if not os.path.exists(ffmpeg_path):
        url = 'https://github.com/GyanD/codexffmpeg/releases/download/2023-10-02-git-9e531370b3/ffmpeg-2023-10-02-git-9e531370b3-essentials_build.zip'
        r = requests.get(url, allow_redirects=True)
        ffmpeg_zip = os.path.join(APP_DIR,"ffmpeg.zip")
        ffmpeg_dir = os.path.join(APP_DIR,"ffmpeg")
        ffmpeg_exe = os.path.join(ffmpeg_dir,"ffmpeg-2023-10-02-git-9e531370b3-essentials_build","bin","ffmpeg.exe")
        with open(ffmpeg_zip, 'wb') as ffmpeg_file:
            ffmpeg_file.write(r.content)
        shutil.unpack_archive(ffmpeg_zip, ffmpeg_dir,"zip")  
        shutil.move(ffmpeg_exe,ffmpeg_path)    
        shutil.rmtree(ffmpeg_dir)
        os.remove(ffmpeg_zip)
    return ffmpeg_path

def get_audio_duration(file_path):
    sample_rate, data = wavfile.read(file_path)
    len_data = len(data)
    duration = int(len_data / sample_rate)
    return duration

def format_duration(time):
    seconds = int(time)
    hours = seconds // 3600  # Divide by 3600 to get the number of hours
    minutes = (seconds % 3600) // 60  # Divide the remaining seconds by 60 to get the number of minutes
    remaining_seconds = seconds % 60  # The remaining seconds
    formatted_time = f"{hours:02d}h {minutes:02d}m {remaining_seconds:02d}s"
    return formatted_time