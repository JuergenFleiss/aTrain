import subprocess
import os
from datetime import datetime
import string

# Assuming segment_duration is defined globally
segment_duration = 360  # Example: 6 minutes 


def split_audio(audio_file, output_dir, segment_duration=360):
    """
    Splits an audio file into segments of a specified duration using ffmpeg,
    and saves them in the provided output directory. Returns a list of paths
    to the generated segments.
    
    Args:
        audio_file (str): Path to the input audio file.
        output_dir (str): Path to the directory where the segments will be saved.
        segment_duration (int): Duration of each audio segment in seconds.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_pattern = os.path.join(output_dir, f"segment_{timestamp}_%03d.wav")

    cmd = [
        'ffmpeg',
        '-i', audio_file,
        '-f', 'segment',
        '-segment_time', str(segment_duration),
        '-c', 'copy',
        '-vn',  # Exclude video
        output_pattern
    ]

    try:
        subprocess.run(cmd, check=True, stderr=subprocess.PIPE, text=True)
        print(f"Audio has been successfully split and saved to {output_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to split audio: {e.stderr}")
        return []

    # Generate the list of file paths for the new audio segments
    segment_files = [os.path.join(output_dir, f) for f in os.listdir(output_dir)
                     if f.startswith(f"segment_{timestamp}") and f.endswith('.wav')]
    return segment_files
    
def clean_filename(filename):
    """
    Remove characters from the filename that are not ASCII letters, digits, underscores, or dots.
    """
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    cleaned_filename = ''.join(c for c in filename if c in valid_chars)
    return cleaned_filename

def safe_rename(file_path):
    """
    Renames the file at file_path after cleaning its name, ensuring it doesn't overwrite an existing file.
    """
    # Extract directory, name, and extension
    directory, filename = os.path.split(file_path)
    name, ext = os.path.splitext(filename)
    
    # Clean the filename
    cleaned_name = clean_filename(name)
    
    # Ensure the new filename doesn't overwrite an existing file
    new_filename = cleaned_name + ext
    new_file_path = os.path.join(directory, new_filename)
    counter = 1
    while os.path.exists(new_file_path):
        new_filename = f"{cleaned_name}({counter}){ext}"
        new_file_path = os.path.join(directory, new_filename)
        counter += 1
    
    # Rename the file
    if new_file_path != file_path:
        os.rename(file_path, new_file_path)
        print(f"File renamed to: {new_file_path}")
        return new_file_path
    else:
        print("No need to rename; file name is already in the desired format.")
        return file_path
        
if __name__ == "__main__":
    # Example usage
    input_audio = "C:/Users/dower/Videos/Why Context Matters When Bridges Burn..._1.mp3"
    output_dir = "C:\\Users\\dower\\Videos\\16-04-112949-Why Context Matters When Bridges Burn..._1"
    segment_duration = 1800  # For example, 1800 seconds (30 minutes)

    split_audio(input_audio, output_dir, segment_duration)
