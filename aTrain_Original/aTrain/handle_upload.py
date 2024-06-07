import os
from .archive import TRANSCRIPT_DIR
from .audio import prepare_audio, get_audio_duration

def get_inputs(request):
    file = request.files["file"]
    model = request.form.get('model')
    language = request.form.get('language')
    speaker_detection = True if request.form.get('speaker_detection') else False
    num_speakers = request.form.get("num_speakers")
    device = "GPU" if request.form.get('GPU') else "CPU"
    compute_type = "float16" if request.form.get('float16') else "int8"
    return file, model, language, speaker_detection, num_speakers, device, compute_type

def check_inputs(file, model, language, num_speakers):
    file_correct = check_file(file)
    model_correct = check_model(model)
    language_correct = check_language(language)
    num_speakers_correct = check_num_speakers(num_speakers)
    return file_correct and model_correct and language_correct and num_speakers_correct

def check_file(file):
    filename = file.filename
    file_extension = os.path.splitext(filename)[1]
    file_extension_lower = str(file_extension).lower()
    correct_file_formats = ['.3dostr', '.4xm', '.aa', '.aac', '.ac3', '.acm', '.act', '.adf', '.adp', '.ads', '.adx', '.aea', '.afc', '.aiff', '.aix', '.alaw', '.alias_pix', '.alp', '.amr', '.amrnb', '.amrwb', '.anm', '.apc', '.ape', '.apm', '.apng', '.aptx', '.aptx_hd', '.aqtitle', '.argo_asf', '.asf', '.asf_o', '.ass', '.ast', '.au', '.av1', '.avi', '.avr', '.avs', '.avs2', '.bethsoftvid', '.bfi', '.bfstm', '.bin', '.bink', '.bit', '.bmp_pipe', '.bmv', '.boa', '.brender_pix', '.brstm', '.c93', '.caf', '.cavsvideo', '.cdg', '.cdxl', '.cine', '.codec2', '.codec2raw', '.concat', '.data', '.daud', '.dcstr', '.dds_pipe', '.derf', '.dfa', '.dhav', '.dirac', '.dnxhd', '.dpx_pipe', '.dsf', '.dsicin', '.dss', '.dts', '.dtshd', '.dv', '.dvbsub', '.dvbtxt', '.dxa', '.ea', '.ea_cdata', '.eac3', '.epaf', '.exr_pipe', '.f32be', '.f32le', '.f64be', '.f64le', '.fbdev', '.ffmetadata', '.film_cpk', '.filmstrip', '.fits', '.flac', '.flic', '.flv', '.frm', '.fsb', '.fwse', '.g722', '.g723_1', '.g726', '.g726le', '.g729', '.gdv', '.genh', '.gif', '.gif_pipe', '.gsm', '.gxf', '.h261', '.h263', '.h264', '.hca', '.hcom', '.hevc', '.hls', '.hnm', '.ico', '.idcin', '.idf', '.iff', '.ifv', '.ilbc', '.image2', '.image2pipe', '.ingenient', '.ipmovie', '.ircam', '.iss', '.iv8', '.ivf', '.ivr', '.j2k_pipe', '.jacosub', '.jpeg_pipe', '.jpegls_pipe', '.jv', '.kux', '.kvag', '.lavfi', '.live_flv', '.lmlm4', '.loas', '.lrc', '.lvf', '.lxf', '.m4v', '.matroska', '.webm', '.mgsts', '.microdvd', '.mjpeg', '.mjpeg_2000', '.mlp', '.mlv', '.mm', '.mmf', '.mov', '.mp4', '.m4a', '.3gp', '.3g2', '.mj2', '.mkv', '.mp3', '.mpc', '.mpc8', '.mpeg', '.mpegts', '.mpegtsraw', '.mpegvideo', '.mpjpeg', '.mpl2', '.mpsub', '.msf', '.msnwctcp', '.mtaf', '.mtv', '.mulaw', '.musx', '.mv', '.mvi', '.mxf', '.mxg', '.nc', '.nistsphere', '.nsp', '.nsv', '.nut', '.nuv', '.ogg', '.oma', '.oss', '.paf', '.pam_pipe', '.pbm_pipe', '.pcx_pipe', '.pgm_pipe', '.pgmyuv_pipe', '.pictor_pipe', '.pjs', '.pmp', '.png_pipe', '.pp_bnk', '.ppm_pipe', '.psd_pipe', '.psxstr', '.pva', '.pvf', '.qcp', '.qdraw_pipe', '.r3d', '.rawvideo', '.realtext', '.redspark', '.rl2', '.rm', '.roq', '.rpl', '.rsd', '.rso', '.rtp', '.rtsp', '.s16be', '.s16le', '.s24be', '.s24le', '.s32be', '.s32le', '.s337m', '.s8', '.sami', '.sap', '.sbc', '.sbg', '.scc', '.sdp', '.sdr2', '.sds', '.sdx', '.ser', '.sgi_pipe', '.shn', '.siff', '.sln', '.smjpeg', '.smk', '.smush', '.sol', '.sox', '.spdif', '.srt', '.stl', '.subviewer', '.subviewer1', '.sunrast_pipe', '.sup', '.svag', '.svg_pipe', '.swf', '.tak', '.tedcaptions', '.thp', '.tiertexseq', '.tiff_pipe', '.tmv', '.truehd', '.tta', '.tty', '.txd', '.ty', '.u16be', '.u16le', '.u24be', '.u24le', '.u32be', '.u32le', '.u8', '.v210', '.v210x', '.vag', '.vc1', '.vc1test', '.vidc', '.video4linux2', '.v4l2', '.vividas', '.vivo', '.vmd', '.vobsub', '.voc', '.vpk', '.vplayer', '.vqf', '.w64', '.wav', '.wc3movie', '.webm_dash_manifest', '.webp_pipe', '.webvtt', '.wsaud', '.wsd', '.wsvqa', '.wtv', '.wv', '.wve', '.xa', '.xbin', '.xmv', '.xpm_pipe', '.xvag', '.xwd_pipe', '.xwma', '.yop', '.yuv4mpegpipe']
    return file_extension_lower in correct_file_formats

def check_model(model):
    correct_models = ["tiny", "base", "small", "medium" , "large-v1" , "large-v2"]
    return model in correct_models

def check_language(language):
    correct_languages = ['auto-detect','af', 'ar', 'hy', 'az', 'be', 'bs', 'bg', 'ca', 'zh', 'hr', 'cs', 'da', 'nl', 'en', 'et', 'fi', 'fr', 'gl', 'de', 'el', 'he', 'hi', 'hu', 'is', 'id', 'it', 'ja', 'kn', 'kk', 'ko', 'lv', 'lt', 'mk', 'ms', 'mr', 'mi', 'ne', 'no', 'fa', 'pl', 'pt', 'ro', 'ru', 'sr', 'sk', 'sl', 'es', 'sw', 'sv', 'tl', 'ta', 'th', 'tr', 'uk', 'ur', 'vi', 'cy']
    return language in correct_languages

def check_num_speakers(num_speakers):
    correct_num_speakers = ["auto-detect","1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
    return num_speakers in correct_num_speakers

def handle_file(file, timestamp, model, device):
    os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
    filename = file.filename
    file_id = create_file_id(filename, timestamp)
    file_directory = os.path.join(TRANSCRIPT_DIR,file_id)
    os.makedirs(file_directory)
    file_path = os.path.join(file_directory, filename)
    file.save(file_path)
    processed_file = prepare_audio(file_id, file_path, file_directory)
    audio_duration = get_audio_duration(processed_file)
    estimated_process_time = estimate_processing_time(audio_duration,model, device)
    os.remove(file_path)
    return filename, file_id, estimated_process_time, audio_duration

def create_file_id(filename, timestamp):
    file_base_name = os.path.normpath(filename)
    short_base_name = file_base_name[0:49] if len(file_base_name) >= 50 else file_base_name
    file_id = timestamp + " " + short_base_name
    return file_id

def estimate_processing_time(duration, model, device):
    match model, device: 
        case "tiny", "CPU": estimate = duration * 0.5
        case "base", "CPU": estimate = duration * 0.75
        case "small", "CPU": estimate = duration * 1
        case "medium", "CPU": estimate = duration * 2
        case "large-v1", "CPU": estimate = duration * 2.75
        case "large-v2", "CPU": estimate = duration * 3.5
        case "tiny", "GPU": estimate = duration * 0.1
        case "base", "GPU": estimate = duration * 0.125
        case "small", "GPU": estimate = duration * 0.15
        case "medium", "GPU": estimate = duration * 0.2
        case "large-v1", "GPU": estimate = duration * 0.25 
        case "large-v2", "GPU": estimate = duration * 0.3
    return estimate

if __name__ == "__main__":
    ...