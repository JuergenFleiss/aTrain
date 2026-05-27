import tempfile
import unittest
from inspect import signature
from pathlib import Path
from unittest import mock

from aTrain.cli import (
    DEFAULT_INIT_MODELS,
    InputFile,
    OutputPlan,
    _copy_outputs,
    _transcribe_one,
    cli,
    transcribe,
)
from aTrain_core.settings import ComputeType, Device
from typer.testing import CliRunner


class CliPathTests(unittest.TestCase):
    def test_transcribe_one_preserves_original_file_path_with_unicode_spaces(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_path = Path(temp_dir) / "录音 (28).m4a"
            audio_path.write_bytes(b"placeholder")
            item = InputFile(audio_path, Path(audio_path.name), Path("."))

            def assert_original_path(path, *args):
                self.assertEqual(str(audio_path), path)

            def assert_original_settings(settings):
                self.assertEqual(audio_path, settings.file)
                self.assertEqual(audio_path.name, settings.file_name)

            with (
                mock.patch("aTrain.cli.check_inputs_transcribe", side_effect=assert_original_path),
                mock.patch(
                    "aTrain_core.transcribe.transcribe", side_effect=assert_original_settings
                ),
            ):
                _transcribe_one(
                    item=item,
                    output_plan=[],
                    overwrite=True,
                    model="large-v3-turbo",
                    language="auto-detect",
                    speaker_detection=False,
                    speaker_count=0,
                    device=Device.CPU,
                    compute_type=ComputeType.FLOAT32,
                    temperature=None,
                    prompt=None,
                    cpu_threads=0,
                )


class CliContractTests(unittest.TestCase):
    def test_default_init_downloads_default_transcription_and_speaker_models(self):
        runner = CliRunner()

        with mock.patch("aTrain.cli.get_model") as get_model:
            result = runner.invoke(cli, ["init"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(
            [call.args[0] for call in get_model.call_args_list],
            list(DEFAULT_INIT_MODELS),
        )

    def test_transcribe_defaults_to_no_overwrite(self):
        self.assertIs(signature(transcribe).parameters["overwrite"].default, False)

    def test_copy_outputs_rejects_existing_target_without_overwrite(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = root / "staging" / "file-id"
            source_dir.mkdir(parents=True)
            (source_dir / "transcription.txt").write_text("new", encoding="utf-8")

            target = root / "out" / "existing.txt"
            target.parent.mkdir()
            target.write_text("old", encoding="utf-8")

            plan = [OutputPlan("txt", "transcription.txt", target)]

            with self.assertRaisesRegex(FileExistsError, "Use --overwrite"):
                _copy_outputs(root / "staging", "file-id", plan, overwrite=False)

            self.assertEqual(target.read_text(encoding="utf-8"), "old")

    def test_macos_freeze_spec_does_not_reference_missing_runtime_hook(self):
        spec = Path("macos_freeze.spec").read_text(encoding="utf-8")

        self.assertIn("runtime_hooks=[]", spec)
        self.assertNotIn("pyi_runtime_model_paths.py", spec)
