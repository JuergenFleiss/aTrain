import traceback
from concurrent.futures.process import BrokenProcessPool
from multiprocessing import Manager
from pathlib import Path
from typing import TypedDict, cast

import numpy as np
from aTrain.components.dialogs.error import dialog_error
from aTrain.components.dialogs.finished import dialog_finished
from aTrain.components.dialogs.process import close_dialog_process, dialog_process
from aTrain.utils.archive import delete_transcription
from aTrain_core import outputs as core_outputs
from aTrain_core.settings import ComputeType, Device, Settings, check_inputs_transcribe
from nicegui import app, events, run, ui
from nicegui.run import SubprocessException
from nicegui.run import setup as setup_process_pool
from starlette.formparsers import MultiPartParser

MultiPartParser.spool_max_size = 1024 * 1024 * 1024 * 10  # 10 GB file size limit


class State(TypedDict):
    model: str
    language: str
    speaker_detection: bool
    speaker_count: float | None
    GPU: bool
    compute_type: str
    temperature_override: float | None
    initial_prompt: str | None
    cpu_threads: int


VOICEPRINT_THRESHOLD = 0.5
VOICEPRINT_MARGIN = 0.05


async def start_transcription(file: events.UploadEventArguments):
    # Lazy import for improved startup speed
    from aTrain_core.transcribe import prepare_transcription

    with Manager() as manager:
        progress = manager.dict({"task": "Prepare", "current": 0, "total": 999999})
        dialog_process(progress)
        _, file_id, timestamp = prepare_transcription(Path(file.name))
        state = cast(State, app.storage.general)
        try:
            settings = Settings(
                file=file.content,
                file_id=file_id,
                file_name=file.name,
                model=state.get("model"),
                language=state.get("language"),
                speaker_detection=state.get("speaker_detection"),
                speaker_count=int(state.get("speaker_count") or 0) or None,
                device=Device.GPU if state.get("GPU") else Device.CPU,
                compute_type=ComputeType(state.get("compute_type")),
                timestamp=timestamp,
                temperature=state.get("temperature_override"),
                initial_prompt=state.get("initial_prompt") or None,
                cpu_threads=int(state.get("cpu_threads", 0)) or 0,
                progress=progress,
            )
            check_inputs_transcribe(
                settings.file_name, settings.model, settings.language, settings.device
            )
            await run.cpu_bound(transcribe_with_voiceprints, settings=settings)
            close_dialog_process()
            dialog_finished(file_id)

        except BrokenProcessPool:
            delete_transcription(file_id)
            setup_process_pool()
            close_dialog_process()
            ui.navigate.reload()

        except SubprocessException as e:
            close_dialog_process()
            dialog_error(error=e.original_message, traceback=e.original_traceback)

        except Exception as e:
            close_dialog_process()
            dialog_error(error=str(e), traceback=traceback.format_exc())


def transcribe_with_voiceprints(settings: Settings) -> None:
    profiles = _list_voiceprints() if settings.speaker_detection else []
    if not profiles:
        _transcribe_core(settings)
        return

    with _patch_core_speaker_capture():
        _transcribe_core(settings)
    _apply_voiceprint_identification_to_output(settings.file_id, profiles)


def _apply_voiceprint_identification_to_output(file_id: str, profiles: list) -> None:
    captured = _read_captured_embeddings(Path(core_outputs.TRANSCRIPT_DIR), file_id)
    if captured is None:
        core_outputs.write_logfile("No speaker embeddings captured for voiceprints", file_id)
        return

    labels, embeddings = captured
    if not labels or not isinstance(embeddings, np.ndarray) or embeddings.size == 0:
        return

    scores = _cosine_similarity_matrix(embeddings, profiles)
    speaker_map = _assign_voiceprints(
        scores,
        labels,
        [profile.name for profile in profiles],
        VOICEPRINT_THRESHOLD,
        VOICEPRINT_MARGIN,
    )
    if not speaker_map:
        core_outputs.write_logfile("No voiceprint matches above threshold", file_id)
        return

    transcript_path = Path(core_outputs.TRANSCRIPT_DIR) / file_id / "transcription.json"
    import json

    with transcript_path.open("r", encoding="utf-8") as handle:
        transcript = json.load(handle)
    _apply_speaker_map_to_transcript(transcript, speaker_map)
    core_outputs.create_output_files(transcript, True, file_id)
    core_outputs.write_logfile(f"Applied voiceprint speaker map: {speaker_map}", file_id)


def _transcribe_core(settings: Settings) -> None:
    from aTrain_core.transcribe import transcribe

    transcribe(settings)


def _list_voiceprints():
    from aTrain.voiceprints import list_voiceprints

    return list_voiceprints()


def _patch_core_speaker_capture():
    from aTrain.voiceprint_identification import patch_core_speaker_capture

    return patch_core_speaker_capture()


def _read_captured_embeddings(staging_dir: Path, file_id: str):
    from aTrain.voiceprint_identification import read_captured_embeddings

    return read_captured_embeddings(staging_dir, file_id)


def _cosine_similarity_matrix(embeddings: np.ndarray, profiles: list):
    from aTrain.voiceprints import cosine_similarity_matrix

    return cosine_similarity_matrix(embeddings, profiles)


def _assign_voiceprints(
    scores: np.ndarray,
    labels: list[str],
    names: list[str],
    threshold: float,
    margin: float,
):
    from aTrain.voiceprints import assign_voiceprints

    return assign_voiceprints(scores, labels, names, threshold, margin)


def _apply_speaker_map_to_transcript(transcript: dict, speaker_map: dict[str, str]) -> None:
    from aTrain.voiceprints import apply_speaker_map_to_transcript

    apply_speaker_map_to_transcript(transcript, speaker_map)
