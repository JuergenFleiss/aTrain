from ffmpeg.nodes import output_operator
from ffmpeg._run import Error, compile
import subprocess

#Customization of ffmpeg-python to fix some issues during code freezing

@output_operator()
def run_async(
    stream_spec,
    cmd='ffmpeg',
    pipe_stdin=False,
    pipe_stdout=False,
    pipe_stderr=False,
    quiet=False,
    overwrite_output=False,
):
    DETACHED_PROCESS = 0x00000008 #added this line to prevent console flickering
    args = compile(stream_spec, cmd, overwrite_output=overwrite_output,)
    stdin_stream = subprocess.PIPE if pipe_stdin else None
    stdout_stream = subprocess.PIPE if pipe_stdout or quiet else None
    stderr_stream = subprocess.PIPE if pipe_stderr or quiet else None
    return subprocess.Popen(args, stdin=stdin_stream, stdout=stdout_stream, stderr=stderr_stream, creationflags=DETACHED_PROCESS)

@output_operator()
def custom_ffmpeg_run(
    stream_spec,
    cmd='ffmpeg',
    capture_stdout=False,
    capture_stderr=False,
    input=None,
    quiet=False,
    overwrite_output=False,
):
    process = run_async(
        stream_spec,
        cmd,
        pipe_stdin=input is not None,
        pipe_stdout=capture_stdout,
        pipe_stderr=capture_stderr,
        quiet=quiet,
        overwrite_output=overwrite_output,
    )
    out, err = process.communicate(input)
    retcode = process.poll()
    if retcode:
        raise Error('ffmpeg', out, err)
    return out, err