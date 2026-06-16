import shutil
import tempfile
import traceback
from datetime import UTC, datetime
from pathlib import Path

from aTrain.model_downloads import check_model_downloaded
from aTrain.voiceprints import (
    EMBEDDING_MODEL_ID,
    VOICEPRINT_SCHEMA_VERSION,
    VoiceprintProfile,
    load_voiceprint,
    merge_centroid,
    remove_voiceprint,
    save_voiceprint,
    validate_voiceprint_name,
)
from aTrain_core.globals import SAMPLING_RATE
from aTrain_core.load_resources import get_model
from nicegui import app, events, run
from nicegui.run import SubprocessException


async def enroll_voiceprint(
    file_event: events.UploadEventArguments, name: str, update: bool
) -> None:
    cleaned_name = validate_voiceprint_name(name)
    check_model_downloaded("speaker-detection")

    tmp_path: Path | None = None
    try:
        suffix = Path(file_event.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            tmp_path = Path(temp_file.name)
            if isinstance(file_event.content, Path):
                temp_file.close()
                shutil.copy2(file_event.content, tmp_path)
            else:
                temp_file.write(file_event.content.read())

        model_path = get_model("speaker-detection")
        duration_sec = _audio_duration_sec(tmp_path)
        device = _enrollment_device()
        from aTrain.voiceprint_identification import extract_embedding

        embedding = await run.cpu_bound(
            extract_embedding,
            audio_path=tmp_path,
            model_path=model_path,
            device=device,
            min_duration_sec=3.0,
        )

        enrollment = {
            "source": file_event.name,
            "duration_sec": round(duration_sec, 2),
            "enrolled_at": datetime.now(UTC).isoformat(),
        }
        try:
            existing = load_voiceprint(cleaned_name)
        except FileNotFoundError:
            existing = None

        if existing is not None and not update:
            raise FileExistsError(
                f"Voiceprint {cleaned_name} already exists. Enable update to add another enrollment."
            )
        if existing is None:
            profile = VoiceprintProfile(
                name=cleaned_name,
                model_id=EMBEDDING_MODEL_ID,
                schema_version=VOICEPRINT_SCHEMA_VERSION,
                embedding_dim=int(embedding.shape[0]),
                embedding=embedding,
                enrollments=[enrollment],
            )
        else:
            profile = VoiceprintProfile(
                name=existing.name,
                model_id=existing.model_id,
                schema_version=existing.schema_version,
                embedding_dim=existing.embedding_dim,
                embedding=merge_centroid(
                    existing.embedding,
                    embedding,
                    existing_count=max(len(existing.enrollments), 1),
                ),
                enrollments=[*existing.enrollments, enrollment],
            )
        save_voiceprint(profile)
    finally:
        if tmp_path is not None and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


async def remove_voiceprint_async(name: str) -> None:
    remove_voiceprint(name)


def show_voiceprint_error(error: Exception) -> None:
    from aTrain.components.dialogs.error import dialog_error

    if isinstance(error, SubprocessException):
        dialog_error(error=error.original_message, traceback=error.original_traceback)
    else:
        dialog_error(error=str(error), traceback=traceback.format_exc())


def _audio_duration_sec(audio_path: Path) -> float:
    from faster_whisper.audio import decode_audio

    audio_array = decode_audio(str(audio_path), sampling_rate=SAMPLING_RATE)
    return len(audio_array) / SAMPLING_RATE


def _enrollment_device():
    import torch

    use_gpu = bool(app.storage.general.get("GPU", False))
    return torch.device("cuda" if use_gpu else "cpu")
