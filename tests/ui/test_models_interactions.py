"""Interaction tests for the /models page.

Drives the Download / Delete buttons on the models page through the
NiceGUI in-process `user` fixture, asserting the page calls the right
backend function with the right argument. The page reads from
`read_model_metadata` and clicks invoke `download_model` /
`remove_model`; all three are monkeypatched so the test doesn't hit
HuggingFace, doesn't spawn a CPU-bound worker for an actual download,
and doesn't depend on which models are present on the host.
"""

import aTrain.pages.models as models_page
import pytest
from nicegui.testing import User

pytestmark = pytest.mark.module_under_test(models_page)


def _fake_metadata():
    """A predictable mix: one downloaded model (large-v1) and one not
    downloaded (tiny). Both are outside REQUIRED_MODELS so the page
    actually renders them as rows."""
    return [
        {"model": "tiny", "size": "75 MB", "downloaded": False},
        {"model": "large-v1", "size": "3 GB", "downloaded": True},
    ]


@pytest.fixture
def mocked_models(monkeypatch):
    """Pin the models the page sees, and record any download/remove calls."""
    download_calls = []
    remove_calls = []

    def _record_download(model):
        # The real download_model is async, but the on_click handler returns
        # whatever the lambda returns and NiceGUI awaits coroutines for us
        # on the live server. In the user fixture the await chain isn't
        # synchronously driven, so we record via a synchronous stub.
        download_calls.append(model)

    def _record_remove(model):
        remove_calls.append(model)

    monkeypatch.setattr(models_page, "read_model_metadata", _fake_metadata)
    monkeypatch.setattr(models_page, "download_model", _record_download)
    monkeypatch.setattr(models_page, "remove_model", _record_remove)
    return download_calls, remove_calls


async def test_models_page_lists_non_required_models(user: User, mocked_models):
    await user.open("/models")
    await user.should_see("Model Manager", retries=100)
    await user.should_see("tiny")
    await user.should_see("large-v1")
    await user.should_see("75 MB")
    await user.should_see("3 GB")


async def test_download_button_invokes_download_model(user: User, mocked_models):
    download_calls, _ = mocked_models
    await user.open("/models")
    await user.should_see("Model Manager", retries=100)
    # Exactly one row is not-downloaded → exactly one "Download" button.
    user.find("Download").click()
    assert download_calls == ["tiny"]


async def test_delete_button_invokes_remove_model(user: User, mocked_models):
    _, remove_calls = mocked_models
    await user.open("/models")
    await user.should_see("Model Manager", retries=100)
    # Exactly one row is downloaded → exactly one "Delete" button.
    user.find("Delete").click()
    assert remove_calls == ["large-v1"]
