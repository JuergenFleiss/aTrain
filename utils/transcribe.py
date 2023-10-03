import os
from flask import render_template
from utils.use_custom_transcriber import use_transcriber
from utils.output_files import create_txt_files
import traceback
from utils.archive import read_metadata, delete_transcription, add_processing_time_to_metadata, TRANSCRIPT_DIR

def handle_transcription(file_id):
    try:
        filename, model, language, speaker_detection, num_speakers = read_metadata(file_id)
        file_directory = os.path.join(TRANSCRIPT_DIR,file_id)
        prepared_file = os.path.join(file_directory, file_id + ".wav")
        for step in use_transcriber(file_directory, prepared_file, model, language, speaker_detection, num_speakers):
            response = f"data: {step['task']}\n\n"
            yield response
        create_txt_files(step["result"], speaker_detection, file_directory, filename)
        add_processing_time_to_metadata(file_id)
        os.remove(prepared_file)
        html = render_template("modal_download.html", file_id=file_id).replace('\n', '')
        response = f"event: stopstream\ndata: {html}\n\n"
        yield response
    except Exception as e:
        delete_transcription(file_id)
        traceback_str = traceback.format_exc()
        error = str(e)
        html = render_template("modal_error.html", error=error, traceback=traceback_str).replace('\n', '')
        response = f"event: stopstream\ndata: {html}\n\n"
        yield response

if __name__ == "__main__":
    ...
    