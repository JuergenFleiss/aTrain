import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from aTrain_core.globals import ATRAIN_DIR
from scipy.optimize import linear_sum_assignment

VOICEPRINTS_DIR = ATRAIN_DIR / "voiceprints"
VOICEPRINT_SCHEMA_VERSION = 1
EMBEDDING_MODEL_ID = "speaker-detection/embedding"
LOGGER = logging.getLogger(__name__)

_INVALID_NAME_CHARS = set('<>:"/\\|?*')


@dataclass
class VoiceprintProfile:
    name: str
    model_id: str
    schema_version: int
    embedding_dim: int
    embedding: np.ndarray
    enrollments: list[dict[str, Any]] = field(default_factory=list)


def validate_voiceprint_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("Voiceprint name cannot be empty.")
    if len(cleaned) > 64:
        raise ValueError("Voiceprint name must be 64 characters or fewer.")
    if any(char in _INVALID_NAME_CHARS for char in cleaned):
        raise ValueError("Voiceprint name cannot contain path or Windows-reserved characters.")
    return cleaned


def voiceprint_path(name: str) -> Path:
    return VOICEPRINTS_DIR / f"{validate_voiceprint_name(name)}.json"


def load_voiceprint(name: str) -> VoiceprintProfile:
    path = voiceprint_path(name)
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return _profile_from_payload(payload, path)


def save_voiceprint(profile: VoiceprintProfile) -> None:
    name = validate_voiceprint_name(profile.name)
    embedding = _l2_normalise_vector(profile.embedding)
    embedding_dim = int(embedding.shape[0])
    VOICEPRINTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": VOICEPRINT_SCHEMA_VERSION,
        "name": name,
        "model_id": profile.model_id,
        "embedding_dim": embedding_dim,
        "embedding": embedding.tolist(),
        "enrollments": list(profile.enrollments),
    }
    path = voiceprint_path(name)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def list_voiceprints() -> list[VoiceprintProfile]:
    if not VOICEPRINTS_DIR.exists():
        return []

    profiles: list[VoiceprintProfile] = []
    for path in sorted(VOICEPRINTS_DIR.glob("*.json"), key=lambda item: item.stem.lower()):
        try:
            with path.open("r", encoding="utf-8") as handle:
                profiles.append(_profile_from_payload(json.load(handle), path))
        except Exception as error:
            LOGGER.warning("Skipping invalid voiceprint profile %s: %s", path, error)
            continue
    return sorted(profiles, key=lambda profile: profile.name.lower())


def remove_voiceprint(name: str) -> None:
    path = voiceprint_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Voiceprint does not exist: {name}")
    path.unlink()


def merge_centroid(existing: np.ndarray, new: np.ndarray, existing_count: int) -> np.ndarray:
    if existing_count < 1:
        raise ValueError("existing_count must be at least 1.")
    existing_vector = np.asarray(existing, dtype=np.float32)
    new_vector = np.asarray(new, dtype=np.float32)
    if existing_vector.shape != new_vector.shape:
        raise ValueError("Embeddings must have the same shape.")
    return ((existing_vector * existing_count) + new_vector) / (existing_count + 1)


def cosine_similarity_matrix(
    speaker_centroids: np.ndarray, voiceprints: list[VoiceprintProfile]
) -> np.ndarray:
    centroids = np.asarray(speaker_centroids, dtype=np.float32)
    if centroids.size == 0 or not voiceprints:
        return np.empty((centroids.shape[0] if centroids.ndim == 2 else 0, 0), dtype=np.float32)
    if centroids.ndim != 2:
        raise ValueError("speaker_centroids must be a 2-D array.")

    centroid_matrix = _l2_normalise_matrix(centroids)
    voiceprint_matrix = _l2_normalise_matrix(
        np.vstack([np.asarray(profile.embedding, dtype=np.float32) for profile in voiceprints])
    )
    return centroid_matrix @ voiceprint_matrix.T


def assign_voiceprints(
    scores: np.ndarray,
    speaker_labels: list[str],
    voiceprint_names: list[str],
    threshold: float,
    margin: float,
) -> dict[str, str]:
    score_matrix = np.asarray(scores, dtype=np.float32)
    if score_matrix.size == 0 or not speaker_labels or not voiceprint_names:
        return {}
    if score_matrix.shape != (len(speaker_labels), len(voiceprint_names)):
        raise ValueError("scores shape must match speaker_labels and voiceprint_names.")

    rows, columns = linear_sum_assignment(-score_matrix)
    assignments: dict[str, str] = {}
    for row, column in zip(rows, columns, strict=True):
        score = float(score_matrix[row, column])
        if score < threshold:
            continue
        if score - _best_competing_score(score_matrix, row, column) < margin:
            continue
        assignments[speaker_labels[row]] = voiceprint_names[column]
    return assignments


def apply_speaker_map_to_transcript(transcript: dict, speaker_map: dict[str, str]) -> None:
    if not speaker_map:
        return
    for segment in transcript.get("segments", []):
        if segment.get("speaker") in speaker_map:
            segment["speaker"] = speaker_map[segment["speaker"]]
        for word in segment.get("words", []):
            if word.get("speaker") in speaker_map:
                word["speaker"] = speaker_map[word["speaker"]]


def _profile_from_payload(payload: dict[str, Any], path: Path) -> VoiceprintProfile:
    if payload.get("schema_version") != VOICEPRINT_SCHEMA_VERSION:
        raise ValueError(f"Unsupported voiceprint schema in {path}")
    if payload.get("model_id") != EMBEDDING_MODEL_ID:
        raise ValueError(f"Unsupported voiceprint model in {path}")

    name = validate_voiceprint_name(str(payload["name"]))
    embedding = np.asarray(payload["embedding"], dtype=np.float32)
    if embedding.ndim != 1:
        raise ValueError(f"Voiceprint embedding must be one-dimensional: {path}")
    embedding_dim = int(payload["embedding_dim"])
    if embedding.shape[0] != embedding_dim:
        raise ValueError(f"Voiceprint embedding_dim does not match embedding length: {path}")
    return VoiceprintProfile(
        name=name,
        model_id=EMBEDDING_MODEL_ID,
        schema_version=VOICEPRINT_SCHEMA_VERSION,
        embedding_dim=embedding_dim,
        embedding=_l2_normalise_vector(embedding),
        enrollments=list(payload.get("enrollments", [])),
    )


def _l2_normalise_vector(vector: np.ndarray) -> np.ndarray:
    array = np.asarray(vector, dtype=np.float32).reshape(-1)
    norm = float(np.linalg.norm(array))
    if norm == 0.0:
        raise ValueError("Embedding cannot be a zero vector.")
    return array / norm


def _l2_normalise_matrix(matrix: np.ndarray) -> np.ndarray:
    array = np.asarray(matrix, dtype=np.float32)
    norms = np.linalg.norm(array, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError("Embedding matrix cannot contain zero vectors.")
    return array / norms


def _best_competing_score(scores: np.ndarray, row: int, column: int) -> float:
    competitors: list[float] = []
    if scores.shape[1] > 1:
        competitors.append(float(np.max(np.delete(scores[row, :], column))))
    if scores.shape[0] > 1:
        competitors.append(float(np.max(np.delete(scores[:, column], row))))
    if not competitors:
        return float("-inf")
    return max(competitors)
