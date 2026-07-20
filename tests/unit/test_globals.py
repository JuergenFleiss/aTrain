"""Unit tests for aTrain_core.globals' REQUIRED_MODELS_DIR resolution.

The constant is computed at import time, so each test re-executes the module
body via importlib.reload with `files("aTrain")` pointed at an isolated temp
dir. Torch- and NiceGUI-free, so they run in the lightweight `unit` CI job.
"""

import importlib
import importlib.resources
from pathlib import Path

import aTrain_core.globals
import pytest


@pytest.fixture
def reload_globals(monkeypatch, tmp_path):
    """Return a function that reloads aTrain_core.globals with `files("aTrain")`
    resolving to the given path. FLATPAK_ID is cleared and ATRAIN_USER_DIR is
    redirected so the reload never touches the real user environment. The
    pristine module is restored on teardown."""

    def _reload(packaged_dir: Path):
        real_files = importlib.resources.files

        def fake_files(package):
            return packaged_dir if package == "aTrain" else real_files(package)

        monkeypatch.delenv("FLATPAK_ID", raising=False)
        monkeypatch.setenv("ATRAIN_USER_DIR", str(tmp_path / "user"))
        monkeypatch.setattr(importlib.resources, "files", fake_files)
        return importlib.reload(aTrain_core.globals)

    yield _reload
    monkeypatch.undo()
    importlib.reload(aTrain_core.globals)


def test_required_models_dir_uses_packaged_dir_when_it_exists(reload_globals, tmp_path):
    packaged = tmp_path / "aTrain" / "required_models"
    packaged.mkdir(parents=True)
    module = reload_globals(tmp_path / "aTrain")
    assert packaged == module.REQUIRED_MODELS_DIR


def test_required_models_dir_falls_back_to_models_dir_when_missing(reload_globals, tmp_path):
    # No required_models dir inside the package location — e.g. an MSIX
    # without pre-populated models, where the install path is read-only and
    # must never be written to.
    module = reload_globals(tmp_path / "aTrain")
    assert module.REQUIRED_MODELS_DIR == module.MODELS_DIR
