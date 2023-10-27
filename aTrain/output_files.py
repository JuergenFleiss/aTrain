import os
import json 

def create_json_file(file_directory, outfile_name, content):
        output_file_text = os.path.join(file_directory,outfile_name)
        with open(output_file_text,"w", encoding="utf-8") as json_file:
            json.dump(content, json_file,ensure_ascii=False)

def create_txt_files (result, speaker_detection, file_directory, orig_filename):
        create_txt_file(result, file_directory, orig_filename, speaker_detection, maxqda=False, timestamps = False)
        create_txt_file(result, file_directory, orig_filename, speaker_detection, maxqda=False, timestamps = True)
        create_txt_file(result, file_directory, orig_filename, speaker_detection, maxqda=True, timestamps = True)

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
                time = segment["start"]
                formatted_time = format_time(time)
                text = f"{formatted_time} - {text}"
            file.write(text + (" " if maxqda else  "\n"))

def format_time(time):
    seconds = int(time)
    hours = seconds // 3600  # Divide by 3600 to get the number of hours
    minutes = (seconds % 3600) // 60  # Divide the remaining seconds by 60 to get the number of minutes
    remaining_seconds = seconds % 60  # The remaining seconds
    formatted_time = "[{:02d}:{:02d}:{:02d}]".format(hours, minutes, remaining_seconds)
    return formatted_time

if __name__ == "__main__":
    ...