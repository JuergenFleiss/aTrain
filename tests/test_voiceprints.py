import json
import tempfile
import unittest
from pathlib import Path

import aTrain.voiceprints as voiceprints
import numpy as np
from aTrain.voiceprints import VoiceprintProfile


class VoiceprintTests(unittest.TestCase):
    def test_validate_voiceprint_name_rejects_path_separators_blank_and_overlong(self):
        invalid_names = ["", "   ", "Ray/Alice", "Ray\\Alice", "Bad<Name>", "x" * 65]

        for name in invalid_names:
            with self.subTest(name=name), self.assertRaises(ValueError):
                voiceprints.validate_voiceprint_name(name)

    def test_validate_voiceprint_name_accepts_unicode(self):
        self.assertEqual(voiceprints.validate_voiceprint_name("雷"), "雷")

    def test_save_and_load_voiceprint_round_trip(self):
        with self._temporary_voiceprints_dir():
            profile = VoiceprintProfile(
                name="Ray",
                model_id=voiceprints.EMBEDDING_MODEL_ID,
                schema_version=voiceprints.VOICEPRINT_SCHEMA_VERSION,
                embedding_dim=2,
                embedding=np.array([3.0, 4.0], dtype=np.float32),
                enrollments=[{"source": "ray.wav", "duration_sec": 12.4}],
            )

            voiceprints.save_voiceprint(profile)
            loaded = voiceprints.load_voiceprint("Ray")

        self.assertEqual(loaded.name, "Ray")
        self.assertEqual(loaded.embedding_dim, 2)
        self.assertEqual(loaded.enrollments, [{"source": "ray.wav", "duration_sec": 12.4}])
        self.assertTrue(np.allclose(loaded.embedding, np.array([0.6, 0.8], dtype=np.float32)))

    def test_save_voiceprint_l2_normalises_embedding(self):
        with self._temporary_voiceprints_dir():
            profile = VoiceprintProfile(
                name="Ray",
                model_id=voiceprints.EMBEDDING_MODEL_ID,
                schema_version=voiceprints.VOICEPRINT_SCHEMA_VERSION,
                embedding_dim=2,
                embedding=np.array([10.0, 0.0], dtype=np.float32),
                enrollments=[],
            )

            voiceprints.save_voiceprint(profile)
            payload = json.loads(voiceprints.voiceprint_path("Ray").read_text(encoding="utf-8"))

        self.assertEqual(payload["embedding"], [1.0, 0.0])

    def test_save_voiceprint_writes_schema_version_and_model_id(self):
        with self._temporary_voiceprints_dir():
            profile = VoiceprintProfile(
                name="Ray",
                model_id=voiceprints.EMBEDDING_MODEL_ID,
                schema_version=voiceprints.VOICEPRINT_SCHEMA_VERSION,
                embedding_dim=2,
                embedding=np.array([1.0, 0.0], dtype=np.float32),
                enrollments=[],
            )

            voiceprints.save_voiceprint(profile)
            payload = json.loads(voiceprints.voiceprint_path("Ray").read_text(encoding="utf-8"))

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["model_id"], "speaker-detection/embedding")

    def test_list_voiceprints_sorted_by_name(self):
        with self._temporary_voiceprints_dir():
            for name in ["Zoe", "Alice"]:
                voiceprints.save_voiceprint(
                    VoiceprintProfile(
                        name=name,
                        model_id=voiceprints.EMBEDDING_MODEL_ID,
                        schema_version=voiceprints.VOICEPRINT_SCHEMA_VERSION,
                        embedding_dim=2,
                        embedding=np.array([1.0, 0.0], dtype=np.float32),
                        enrollments=[],
                    )
                )

            names = [profile.name for profile in voiceprints.list_voiceprints()]

        self.assertEqual(names, ["Alice", "Zoe"])

    def test_remove_voiceprint_missing_raises(self):
        with self._temporary_voiceprints_dir(), self.assertRaises(FileNotFoundError):
            voiceprints.remove_voiceprint("Ray")

    def test_merge_centroid_running_mean(self):
        merged = voiceprints.merge_centroid(
            np.array([1.0, 0.0], dtype=np.float32),
            np.array([0.0, 1.0], dtype=np.float32),
            existing_count=2,
        )

        self.assertTrue(np.allclose(merged, np.array([2 / 3, 1 / 3], dtype=np.float32)))

    def test_cosine_similarity_matrix_known_values(self):
        centroids = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
        profiles = [
            VoiceprintProfile(
                "Ray", voiceprints.EMBEDDING_MODEL_ID, 1, 2, np.array([1.0, 0.0]), []
            ),
            VoiceprintProfile(
                "Alice", voiceprints.EMBEDDING_MODEL_ID, 1, 2, np.array([0.0, 1.0]), []
            ),
        ]

        scores = voiceprints.cosine_similarity_matrix(centroids, profiles)

        self.assertTrue(np.allclose(scores, np.eye(2, dtype=np.float32)))

    def test_assign_voiceprints_above_threshold_with_margin(self):
        scores = np.array([[0.91, 0.3], [0.2, 0.88]], dtype=np.float32)

        result = voiceprints.assign_voiceprints(
            scores,
            ["SPEAKER_00", "SPEAKER_01"],
            ["Ray", "Alice"],
            threshold=0.5,
            margin=0.05,
        )

        self.assertEqual(result, {"SPEAKER_00": "Ray", "SPEAKER_01": "Alice"})

    def test_assign_voiceprints_rejects_when_margin_violated(self):
        scores = np.array([[0.91, 0.89]], dtype=np.float32)

        result = voiceprints.assign_voiceprints(
            scores,
            ["SPEAKER_00"],
            ["Ray", "Alice"],
            threshold=0.5,
            margin=0.05,
        )

        self.assertEqual(result, {})

    def test_assign_voiceprints_resolves_mutual_exclusivity_via_bipartite(self):
        scores = np.array([[0.9, 0.9], [0.9, 0.1]], dtype=np.float32)

        result = voiceprints.assign_voiceprints(
            scores,
            ["SPEAKER_00", "SPEAKER_01"],
            ["Ray", "Alice"],
            threshold=0.5,
            margin=0.0,
        )

        self.assertEqual(result, {"SPEAKER_00": "Alice", "SPEAKER_01": "Ray"})

    def test_assign_voiceprints_more_speakers_than_voiceprints(self):
        scores = np.array([[0.9], [0.1]], dtype=np.float32)

        result = voiceprints.assign_voiceprints(
            scores,
            ["SPEAKER_00", "SPEAKER_01"],
            ["Ray"],
            threshold=0.5,
            margin=0.0,
        )

        self.assertEqual(result, {"SPEAKER_00": "Ray"})

    def test_assign_voiceprints_empty_voiceprints_returns_empty(self):
        scores = np.empty((2, 0), dtype=np.float32)

        result = voiceprints.assign_voiceprints(
            scores,
            ["SPEAKER_00", "SPEAKER_01"],
            [],
            threshold=0.5,
            margin=0.05,
        )

        self.assertEqual(result, {})

    def test_apply_speaker_map_renames_segment_and_word_speakers_only(self):
        transcript = {
            "segments": [
                {
                    "speaker": "SPEAKER_00",
                    "text": "SPEAKER_00 said hello",
                    "words": [
                        {"speaker": "SPEAKER_00", "word": "hello"},
                        {"speaker": "SPEAKER_01", "word": "there"},
                    ],
                }
            ]
        }

        voiceprints.apply_speaker_map_to_transcript(transcript, {"SPEAKER_00": "Ray"})

        segment = transcript["segments"][0]
        self.assertEqual(segment["speaker"], "Ray")
        self.assertEqual(segment["text"], "SPEAKER_00 said hello")
        self.assertEqual(segment["words"][0]["speaker"], "Ray")
        self.assertEqual(segment["words"][1]["speaker"], "SPEAKER_01")

    def _temporary_voiceprints_dir(self):
        return TemporaryVoiceprintsDir()


class TemporaryVoiceprintsDir:
    def __enter__(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original = voiceprints.VOICEPRINTS_DIR
        voiceprints.VOICEPRINTS_DIR = Path(self.temp_dir.name)
        return voiceprints.VOICEPRINTS_DIR

    def __exit__(self, exc_type, exc, tb):
        voiceprints.VOICEPRINTS_DIR = self.original
        self.temp_dir.cleanup()
