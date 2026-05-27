from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace

from aTrain.components.settings.file import input_file
from aTrain.utils.voiceprints import enroll_voiceprint, show_voiceprint_error
from aTrain.voiceprints import validate_voiceprint_name
from aTrain_core.globals import FLATPAK
from nicegui import events, ui


def enroll_dialog(
    existing_names: set[str],
    on_success: Callable[[], None] | None = None,
) -> None:
    with ui.dialog(value=True) as dialog, ui.card().classes("w-[520px] p-8 gap-4"):
        dialog.props("persistent")
        ui.label("Enroll speaker voiceprint").classes("font-bold text-dark text-lg")
        ui.separator()
        name_input = ui.input("Name").classes("w-full")
        name_error = ui.label("").classes("text-negative text-xs")
        update_toggle = ui.checkbox("Update existing voiceprint")

        with ui.column().classes("gap-2 w-full"):
            ui.label("Reference audio").classes("font-bold text-dark text-sm")
            uploader = input_file()

        ui.label("Use a 10-30s clean clip recorded with a similar microphone.").classes(
            "text-xs text-grey"
        )
        ui.separator()
        with ui.row().classes("w-full justify-end"):
            cancel_button = ui.button("Cancel", color="gray-100")
            cancel_button.props("unelevated no-caps text-color=dark")
            submit_button = ui.button("Enroll", color="dark")
            submit_button.props("unelevated no-caps")

    def validate_form() -> bool:
        try:
            cleaned = validate_voiceprint_name(name_input.value or "")
        except ValueError as error:
            name_error.set_text(str(error))
            return False
        if cleaned not in existing_names and update_toggle.value:
            name_error.set_text("No existing voiceprint with this name.")
            return False
        name_error.set_text("")
        return True

    async def handle_upload(file_event: events.UploadEventArguments) -> None:
        processing = _processing_dialog()
        try:
            await enroll_voiceprint(
                file_event,
                name=name_input.value or "",
                update=bool(update_toggle.value),
            )
            processing.close()
            dialog.close()
            ui.notify("Voiceprint saved", type="positive")
            if on_success is not None:
                on_success()
        except Exception as error:
            processing.close()
            show_voiceprint_error(error)

    async def submit() -> None:
        if not validate_form():
            return
        if FLATPAK:
            selected_path = getattr(uploader, "selected_path", None)
            if not selected_path:
                ui.notify("Select a reference audio file first", type="warning")
                return
            payload = SimpleNamespace(
                name=getattr(uploader, "selected_name", None) or Path(selected_path).name,
                content=Path(selected_path),
            )
            await handle_upload(payload)
            return
        if getattr(uploader, "file_text", "") != "1 File Added":
            ui.notify("Select a reference audio file first", type="warning")
            return
        uploader.upload()

    name_input.on("update:model-value", lambda _: validate_form())
    uploader.on_upload(handle_upload)
    cancel_button.on_click(dialog.close)
    submit_button.on_click(submit)


def _processing_dialog():
    with ui.dialog(value=True) as dialog, ui.card().classes("w-[420px] p-8 gap-3"):
        dialog.props("persistent")
        ui.label("Creating voiceprint").classes("font-bold text-dark text-lg")
        ui.separator()
        ui.spinner(size="lg", color="dark").classes("mx-auto")
        ui.label("Extracting the speaker embedding...").classes("text-sm text-grey")
    return dialog
