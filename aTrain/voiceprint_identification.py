from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import numpy as np
from aTrain_core import outputs as core_outputs
from aTrain_core.globals import SAMPLING_RATE
from aTrain_core.load_resources import get_model
from aTrain_core.outputs import (
    assign_word_speakers,
    transform_speakers_results,
    write_logfile,
)
from aTrain_core.settings import Device, Settings

from aTrain.voiceprints import _l2_normalise_vector

CAPTURE_FILENAME = "_speaker_embeddings.npz"


def extract_embedding(
    audio_path: Path,
    model_path: Path,
    device,
    min_duration_sec: float = 3.0,
) -> np.ndarray:
    audio_array = _decode_audio(str(audio_path), sampling_rate=SAMPLING_RATE)
    duration_sec = len(audio_array) / SAMPLING_RATE
    if duration_sec < min_duration_sec:
        raise ValueError(
            f"Voiceprint enrollment audio must be at least {min_duration_sec:.1f} seconds."
        )

    import torch

    embedding_model = _pretrained_speaker_embedding(str(model_path / "embedding"), device=device)
    waveform = torch.from_numpy(audio_array.astype(np.float32)[None, None, :])
    embedding = embedding_model(waveform)
    if hasattr(embedding, "detach"):
        embedding = embedding.detach().cpu().numpy()
    embedding_array = np.asarray(embedding, dtype=np.float32)
    if embedding_array.ndim == 2:
        embedding_array = embedding_array[0]
    return _l2_normalise_vector(embedding_array).astype(np.float32)


def run_speaker_detection_with_capture(
    settings: Settings, audio_duration: int, audio_array: np.ndarray, transcript: dict
) -> dict:
    """Run speaker detection and capture embeddings.

    This mirrors aTrain_core release_v1.4.2's run_speaker_detection implementation
    and additionally stores DiarizeOutput.speaker_embeddings in the staging
    transcript directory for CLI identity post-processing.
    """
    import torch

    model_path = get_model("speaker-detection")
    write_logfile("Speaker detection model loaded", settings.file_id)
    audio = {
        "waveform": torch.from_numpy(audio_array[None, :]),
        "sample_rate": SAMPLING_RATE,
    }
    pipeline = _pipeline_from_pretrained(model_path)
    if not pipeline:
        raise Exception("Failed to initialize speaker detection pipeline!")
    write_logfile("Detecting speakers", settings.file_id)

    if settings.device == Device.GPU:
        pipeline.to(torch.device("cuda"))

    with _custom_progress_hook(settings.progress) as hook:
        output = pipeline(audio, num_speakers=settings.speaker_count, hook=hook)

    _write_captured_embeddings(settings.file_id, output)
    segments = output.speaker_diarization
    speaker_results = transform_speakers_results(segments)
    write_logfile("Transformed diarization segments", settings.file_id)
    transcript_with_speaker = assign_word_speakers(speaker_results, transcript)
    write_logfile("Assigned speakers to words", settings.file_id)
    return transcript_with_speaker


@contextmanager
def patch_core_speaker_capture() -> Iterator[None]:
    import aTrain_core.transcribe as core_transcribe

    original = core_transcribe.run_speaker_detection
    core_transcribe.run_speaker_detection = run_speaker_detection_with_capture
    try:
        yield
    finally:
        core_transcribe.run_speaker_detection = original


def read_captured_embeddings(
    staging_dir: Path, file_id: str
) -> tuple[list[str], np.ndarray] | None:
    path = staging_dir / file_id / CAPTURE_FILENAME
    if not path.exists():
        return None
    with np.load(path, allow_pickle=False) as data:
        labels = [str(label) for label in data["labels"].tolist()]
        embeddings = np.asarray(data["embeddings"], dtype=np.float32)
    return labels, embeddings


def _write_captured_embeddings(file_id: str, output) -> None:
    labels = [str(label) for label in output.speaker_diarization.labels()]
    embeddings = np.asarray(output.speaker_embeddings, dtype=np.float32)
    target_dir = Path(core_outputs.TRANSCRIPT_DIR) / file_id
    target_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        target_dir / CAPTURE_FILENAME,
        labels=np.asarray(labels),
        embeddings=embeddings,
    )


def _decode_audio(path: str, sampling_rate: int) -> np.ndarray:
    from faster_whisper.audio import decode_audio

    return decode_audio(path, sampling_rate=sampling_rate)


def _pretrained_speaker_embedding(embedding: str, device):
    from pyannote.audio.pipelines.speaker_verification import PretrainedSpeakerEmbedding

    return PretrainedSpeakerEmbedding(embedding, device=device)


def _pipeline_from_pretrained(model_path: Path):
    from pyannote.audio import Pipeline

    return Pipeline.from_pretrained(model_path)


def _custom_progress_hook(progress):
    from aTrain_core.transcribe import CustomProgressHook

    return CustomProgressHook(progress)
