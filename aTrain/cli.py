import shutil
import sys
import tempfile
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import typer
from aTrain_core.globals import (
    DEFAULT_CPU_THREADS,
    MAX_CPU_THREADS,
    MODELS_DIR,
    REQUIRED_MODELS,
    REQUIRED_MODELS_DIR,
)
from aTrain_core.load_resources import download_all_models, get_model, load_model_config_file
from aTrain_core.settings import (
    ComputeType,
    Device,
    Settings,
    check_file,
    check_inputs_transcribe,
)

cli = typer.Typer(help="CLI for aTrain.", no_args_is_help=True)

FORMAT_OUTPUTS = {
    "json": ("transcription.json", "{stem}.json"),
    "txt": ("transcription.txt", "{stem}.txt"),
    "timestamps": ("transcription_timestamps.txt", "{stem}_timestamps.txt"),
    "maxqda": ("transcription_maxqda.txt", "{stem}_maxqda.txt"),
    "srt": ("transcription.srt", "{stem}.srt"),
}
ALLOWED_FORMATS = ",".join(FORMAT_OUTPUTS)
DEFAULT_FORMATS = "txt,timestamps"
DEFAULT_TRANSCRIPTION_MODEL = "large-v3"
DEFAULT_INIT_MODELS = (DEFAULT_TRANSCRIPTION_MODEL, "speaker-detection")


@dataclass(frozen=True)
class InputFile:
    path: Path
    display_path: Path
    relative_dir: Path


@dataclass(frozen=True)
class OutputPlan:
    format_key: str
    source_name: str
    target_path: Path


@dataclass
class FileResult:
    path: Path
    ok: bool
    reason: str = ""
    staging_dir: Path | None = None


class CliTranscriptionError(Exception):
    def __init__(self, message: str, staging_dir: Path | None = None):
        super().__init__(message)
        self.staging_dir = staging_dir


def _parse_formats(value: str) -> list[str]:
    parsed = [part.strip().lower() for part in value.split(",") if part.strip()]
    if not parsed:
        raise ValueError("No output formats specified.")
    invalid = [item for item in parsed if item not in FORMAT_OUTPUTS]
    if invalid:
        allowed = ", ".join(FORMAT_OUTPUTS)
        raise ValueError(f"Unsupported output format(s): {', '.join(invalid)}. Allowed: {allowed}")
    return list(dict.fromkeys(parsed))


def _is_supported_file(path: Path) -> bool:
    return path.is_file() and check_file(path.name)


def _collect_inputs(input_path: Path, recursive: bool) -> tuple[list[InputFile], list[Path]]:
    if not input_path.exists():
        raise ValueError(f"Input does not exist: {input_path}")

    if input_path.is_file():
        if not _is_supported_file(input_path):
            raise ValueError(f"Input file extension is not supported: {input_path}")
        return [InputFile(input_path, Path(input_path.name), Path("."))], []

    if not input_path.is_dir():
        raise ValueError(f"Input is neither a file nor a directory: {input_path}")

    root = input_path.resolve()
    candidates = root.rglob("*") if recursive else root.iterdir()
    files = [path for path in candidates if path.is_file()]
    inputs: list[InputFile] = []
    skipped: list[Path] = []
    for path in sorted(files, key=lambda item: str(item).lower()):
        if not _is_supported_file(path):
            skipped.append(path)
            continue
        relative_dir = path.parent.resolve().relative_to(root) if recursive else Path(".")
        display_path = relative_dir / path.name if relative_dir != Path(".") else Path(path.name)
        inputs.append(InputFile(path, display_path, relative_dir))

    if not inputs:
        raise ValueError(f"No supported audio/video files found in: {input_path}")

    return inputs, skipped


def _resolve_output_dirs(
    output: Path,
    json_output: Path | None,
    txt_output: Path | None,
    timestamps_output: Path | None,
    maxqda_output: Path | None,
    srt_output: Path | None,
) -> dict[str, Path]:
    return {
        "json": json_output or output,
        "txt": txt_output or output,
        "timestamps": timestamps_output or output,
        "maxqda": maxqda_output or output,
        "srt": srt_output or output,
    }


def _build_output_plan(
    item: InputFile, formats: list[str], output_dirs: dict[str, Path]
) -> list[OutputPlan]:
    plans = []
    for format_key in formats:
        source_name, target_template = FORMAT_OUTPUTS[format_key]
        target_dir = output_dirs[format_key] / item.relative_dir
        target_name = target_template.format(stem=item.path.stem)
        plans.append(OutputPlan(format_key, source_name, target_dir / target_name))
    return plans


def _check_model_downloaded(model: str) -> None:
    available_models = load_model_config_file()
    if model not in available_models:
        raise ValueError(f"Model {model} is not available.")

    models_dir = REQUIRED_MODELS_DIR if model in REQUIRED_MODELS else MODELS_DIR
    model_path = models_dir / model
    if not model_path.exists() or not any(model_path.rglob("*.bin")):
        raise FileNotFoundError(f"Model {model} is not downloaded. Run: aTrain-cli init {model}")


def _copy_outputs(
    staging_dir: Path,
    file_id: str,
    output_plan: list[OutputPlan],
    overwrite: bool,
) -> None:
    source_dir = staging_dir / file_id
    for planned in output_plan:
        source_path = source_dir / planned.source_name
        if not source_path.exists():
            raise FileNotFoundError(
                f"Expected {planned.format_key} output was not created: {source_path}"
            )
        if planned.target_path.exists() and not overwrite:
            raise FileExistsError(
                f"Target file exists: {planned.target_path}. Use --overwrite to replace it."
            )

    for planned in output_plan:
        planned.target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_dir / planned.source_name, planned.target_path)


def _transcribe_one(
    item: InputFile,
    output_plan: list[OutputPlan],
    overwrite: bool,
    model: str,
    language: str,
    speaker_detection: bool,
    speaker_count: int,
    device: Device,
    compute_type: ComputeType,
    temperature: float | None,
    prompt: str | None,
    cpu_threads: int,
) -> Path:
    for planned in output_plan:
        if planned.target_path.exists() and not overwrite:
            raise FileExistsError(
                f"Target file exists: {planned.target_path}. Use --overwrite to replace it."
            )

    from aTrain_core import outputs as core_outputs
    from aTrain_core.transcribe import prepare_transcription
    from aTrain_core.transcribe import transcribe as transcribe_core

    staging_dir = Path(tempfile.mkdtemp(prefix="atrain-cli-"))
    original_transcript_dir = core_outputs.TRANSCRIPT_DIR
    gpu_log_dir: Path | None = None
    gpu_log_dir_created = False
    core_outputs.TRANSCRIPT_DIR = str(staging_dir)
    try:
        _, file_id, timestamp = prepare_transcription(item.path)
        # prepare_transcription sanitizes names for file_id; decoding must use the real path.
        file = item.path
        if device == Device.GPU:
            gpu_log_dir = Path(original_transcript_dir) / file_id
            if not gpu_log_dir.exists():
                gpu_log_dir.mkdir(parents=True, exist_ok=True)
                gpu_log_dir_created = True
        check_inputs_transcribe(str(file), model, language, device)
        settings = Settings(
            file=file,
            file_id=file_id,
            file_name=file.name,
            model=model,
            language=language,
            speaker_detection=speaker_detection,
            speaker_count=speaker_count or None,
            device=device,
            compute_type=compute_type,
            timestamp=timestamp,
            temperature=temperature,
            initial_prompt=prompt,
            progress={},
            cpu_threads=cpu_threads,
        )
        transcribe_core(settings)
        _copy_outputs(staging_dir, file_id, output_plan, overwrite)
        shutil.rmtree(staging_dir, ignore_errors=True)
        return staging_dir
    except Exception as error:
        raise CliTranscriptionError(str(error), staging_dir) from error
    finally:
        core_outputs.TRANSCRIPT_DIR = original_transcript_dir
        if gpu_log_dir_created and gpu_log_dir is not None:
            shutil.rmtree(gpu_log_dir, ignore_errors=True)


def _run_batch(
    inputs: list[InputFile],
    skipped: list[Path],
    formats: list[str],
    output_dirs: dict[str, Path],
    overwrite: bool,
    model: str,
    language: str,
    speaker_detection: bool,
    speaker_count: int,
    device: Device,
    compute_type: ComputeType,
    temperature: float | None,
    prompt: str | None,
    cpu_threads: int,
) -> int:
    results: list[FileResult] = []
    total = len(inputs)

    for index, item in enumerate(inputs, 1):
        output_plan = _build_output_plan(item, formats, output_dirs)
        typer.echo(f"[{index}/{total}] start: {item.display_path}")
        started = time.monotonic()
        staging_dir: Path | None = None
        try:
            staging_dir = _transcribe_one(
                item=item,
                output_plan=output_plan,
                overwrite=overwrite,
                model=model,
                language=language,
                speaker_detection=speaker_detection,
                speaker_count=speaker_count,
                device=device,
                compute_type=compute_type,
                temperature=temperature,
                prompt=prompt,
                cpu_threads=cpu_threads,
            )
            elapsed = int(time.monotonic() - started)
            typer.echo(f"[{index}/{total}] done: {item.display_path} ({elapsed}s)")
            results.append(FileResult(item.path, ok=True))
        except Exception as error:
            elapsed = int(time.monotonic() - started)
            reason = str(error)
            staging_dir = getattr(error, "staging_dir", staging_dir)
            typer.echo(
                f"[{index}/{total}] FAIL: {item.display_path} ({elapsed}s) - {reason}",
                err=True,
            )
            traceback.print_exc(file=sys.stderr)
            results.append(FileResult(item.path, ok=False, reason=reason, staging_dir=staging_dir))

    succeeded = sum(1 for result in results if result.ok)
    failed = len(results) - succeeded
    _print_summary(results, skipped)

    if failed and succeeded:
        return 1
    if failed or not succeeded:
        return 2
    return 0


def _print_summary(results: list[FileResult], skipped: list[Path]) -> None:
    succeeded = sum(1 for result in results if result.ok)
    failed = len(results) - succeeded
    typer.echo("\nSummary:")
    typer.echo(f"  total:     {len(results)}")
    typer.echo(f"  succeeded: {succeeded}")
    typer.echo(f"  failed:    {failed}")
    typer.echo(f"  skipped:   {len(skipped)}")

    if skipped:
        typer.echo("Skipped:")
        for path in skipped:
            typer.echo(f"  - {path} - extension not supported")

    failures = [result for result in results if not result.ok]
    if failures:
        typer.echo("Failures:", err=True)
        for result in failures:
            staging = f"; staging={result.staging_dir}" if result.staging_dir else ""
            typer.echo(f"  - {result.path} - {result.reason}{staging}", err=True)


@cli.command()
def transcribe(
    input_path: Annotated[
        Path, typer.Argument(help="Audio/video file or directory to transcribe.", metavar="INPUT")
    ],
    model: Annotated[
        str, typer.Option(help="Whisper model used to transcribe.")
    ] = DEFAULT_TRANSCRIPTION_MODEL,
    language: Annotated[str, typer.Option(help="Language of the audio.")] = "auto-detect",
    prompt: Annotated[str | None, typer.Option(help="Initial prompt passed to model.")] = None,
    speaker_detection: Annotated[
        bool,
        typer.Option(
            "--speaker-detection/--no-speaker-detection",
            help="Enable speaker detection.",
        ),
    ] = True,
    speaker_count: Annotated[
        int,
        typer.Option(help="Number of speakers. Use 0 to let aTrain auto-detect."),
    ] = 0,
    device: Annotated[Device, typer.Option(help="Hardware used to transcribe.")] = Device.GPU,
    compute_type: Annotated[
        ComputeType, typer.Option(help="Data type used in computations.")
    ] = ComputeType.FLOAT32,
    temperature: Annotated[
        float | None, typer.Option(help="Temperature used for sampling.", min=0.0, max=1.0)
    ] = None,
    cpu_threads: Annotated[
        int,
        typer.Option(
            help=f"Number of CPU threads to use (0 = auto, default is {DEFAULT_CPU_THREADS}).",
            min=0,
            max=MAX_CPU_THREADS,
        ),
    ] = DEFAULT_CPU_THREADS,
    recursive: Annotated[
        bool, typer.Option(help="Recursively scan directories for supported files.")
    ] = False,
    formats: Annotated[
        str,
        typer.Option(help=f"Comma-separated output formats. Allowed: {ALLOWED_FORMATS}."),
    ] = DEFAULT_FORMATS,
    output: Annotated[Path, typer.Option(help="Default output directory.")] = Path("atrain-output"),
    json_output: Annotated[Path | None, typer.Option(help="JSON output directory.")] = None,
    txt_output: Annotated[Path | None, typer.Option(help="Plain TXT output directory.")] = None,
    timestamps_output: Annotated[
        Path | None, typer.Option(help="Timestamped TXT output directory.")
    ] = None,
    maxqda_output: Annotated[Path | None, typer.Option(help="MAXQDA TXT output directory.")] = None,
    srt_output: Annotated[Path | None, typer.Option(help="SRT output directory.")] = None,
    overwrite: Annotated[bool, typer.Option(help="Overwrite existing output files.")] = False,
):
    """Transcribe a single file or a directory of files."""
    try:
        selected_formats = _parse_formats(formats)
        inputs, skipped = _collect_inputs(input_path, recursive)
        _check_model_downloaded(model)
        if speaker_detection:
            _check_model_downloaded("speaker-detection")
        output_dirs = _resolve_output_dirs(
            output=output,
            json_output=json_output,
            txt_output=txt_output,
            timestamps_output=timestamps_output,
            maxqda_output=maxqda_output,
            srt_output=srt_output,
        )
    except Exception as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=2) from error

    exit_code = _run_batch(
        inputs=inputs,
        skipped=skipped,
        formats=selected_formats,
        output_dirs=output_dirs,
        overwrite=overwrite,
        model=model,
        language=language,
        speaker_detection=speaker_detection,
        speaker_count=speaker_count,
        device=device,
        compute_type=compute_type,
        temperature=temperature,
        prompt=prompt,
        cpu_threads=cpu_threads,
    )
    raise typer.Exit(code=exit_code)


@cli.command()
def init(
    model: Annotated[
        str, typer.Argument(help="Model to download, 'default', or 'all'.")
    ] = "default",
):
    """Download a model for CLI/GUI use."""
    try:
        if model == "all":
            download_all_models()
            typer.echo("All models downloaded")
        elif model == "default":
            for model_name in DEFAULT_INIT_MODELS:
                get_model(model_name)
            typer.echo("Default CLI models downloaded")
        else:
            get_model(model)
            typer.echo(f"Model {model} downloaded")
    except Exception as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=2) from error


if __name__ == "__main__":
    cli()
