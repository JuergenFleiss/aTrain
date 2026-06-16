import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

import aTrain.voiceprint_identification as voiceprint_identification
import numpy as np
from aTrain_core.globals import SAMPLING_RATE
from aTrain_core.settings import Device


class VoiceprintIdentificationTests(unittest.TestCase):
    def test_extract_embedding_calls_pretrained_with_local_path_and_returns_normalised(self):
        device = object()
        embedding_fn = mock.Mock(return_value=np.array([[3.0, 4.0]], dtype=np.float32))

        with (
            mock.patch(
                "aTrain.voiceprint_identification._decode_audio",
                return_value=np.ones(SAMPLING_RATE * 4, dtype=np.float32),
            ),
            mock.patch(
                "aTrain.voiceprint_identification._pretrained_speaker_embedding",
                return_value=embedding_fn,
            ) as embedding_factory,
        ):
            result = voiceprint_identification.extract_embedding(
                Path("ray.wav"), Path("speaker-detection"), device=device
            )

        embedding_factory.assert_called_once_with(
            str(Path("speaker-detection") / "embedding"), device=device
        )
        self.assertTrue(np.allclose(result, np.array([0.6, 0.8], dtype=np.float32)))
        self.assertEqual(result.dtype, np.float32)

    def test_extract_embedding_raises_on_too_short_audio(self):
        with (
            mock.patch(
                "aTrain.voiceprint_identification._decode_audio",
                return_value=np.ones(SAMPLING_RATE * 2, dtype=np.float32),
            ),
            self.assertRaisesRegex(ValueError, "at least 3.0 seconds"),
        ):
            voiceprint_identification.extract_embedding(
                Path("short.wav"), Path("speaker-detection"), device=object()
            )

    def test_patch_core_speaker_capture_restores_original(self):
        import aTrain_core.transcribe as core_transcribe

        original = core_transcribe.run_speaker_detection
        with voiceprint_identification.patch_core_speaker_capture():
            self.assertIsNot(core_transcribe.run_speaker_detection, original)

        self.assertIs(core_transcribe.run_speaker_detection, original)

    def test_patch_core_speaker_capture_restores_on_exception(self):
        import aTrain_core.transcribe as core_transcribe

        original = core_transcribe.run_speaker_detection
        with (
            self.assertRaises(RuntimeError),
            voiceprint_identification.patch_core_speaker_capture(),
        ):
            raise RuntimeError("boom")

        self.assertIs(core_transcribe.run_speaker_detection, original)

    def test_run_speaker_detection_with_capture_writes_npz(self):
        settings = types.SimpleNamespace(
            file_id="file-id",
            speaker_count=None,
            device=Device.CPU,
            progress={},
        )
        transcript = {"segments": [{"start": 0.0, "end": 1.0, "text": "hello"}]}
        fake_output = types.SimpleNamespace(
            speaker_diarization=FakeDiarization(["SPEAKER_00", "SPEAKER_01"]),
            speaker_embeddings=np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32),
        )
        fake_pipeline = mock.Mock(return_value=fake_output)
        expected_transcript = {"segments": [{"speaker": "SPEAKER_00"}]}

        with tempfile.TemporaryDirectory() as temp_dir:
            (Path(temp_dir) / "file-id").mkdir()
            with (
                mock.patch(
                    "aTrain.voiceprint_identification.core_outputs.TRANSCRIPT_DIR",
                    temp_dir,
                ),
                mock.patch(
                    "aTrain.voiceprint_identification.get_model",
                    return_value=Path("speaker-detection"),
                ),
                mock.patch(
                    "aTrain.voiceprint_identification._pipeline_from_pretrained",
                    return_value=fake_pipeline,
                ),
                mock.patch("aTrain.voiceprint_identification.write_logfile"),
                mock.patch(
                    "aTrain.voiceprint_identification.transform_speakers_results",
                    return_value="speaker-results",
                ),
                mock.patch(
                    "aTrain.voiceprint_identification.assign_word_speakers",
                    return_value=expected_transcript,
                ),
            ):
                result = voiceprint_identification.run_speaker_detection_with_capture(
                    settings,
                    audio_duration=1,
                    audio_array=np.ones(SAMPLING_RATE, dtype=np.float32),
                    transcript=transcript,
                )

            with np.load(Path(temp_dir) / "file-id" / "_speaker_embeddings.npz") as captured:
                labels = captured["labels"].tolist()
                embeddings_shape = captured["embeddings"].shape

        self.assertEqual(result, expected_transcript)
        self.assertEqual(labels, ["SPEAKER_00", "SPEAKER_01"])
        self.assertEqual(embeddings_shape, (2, 2))

    def test_read_captured_embeddings_returns_none_when_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = voiceprint_identification.read_captured_embeddings(Path(temp_dir), "missing")

        self.assertIsNone(result)


class FakeDiarization:
    def __init__(self, labels):
        self._labels = labels

    def labels(self):
        return self._labels
