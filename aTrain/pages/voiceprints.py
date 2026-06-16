from aTrain.components.voiceprints.enroll_dialog import enroll_dialog
from aTrain.layouts.base import base_layout
from aTrain.utils.voiceprints import remove_voiceprint_async, show_voiceprint_error
from aTrain.voiceprints import list_voiceprints
from nicegui import ui


@ui.page("/voiceprints")
def page():
    profiles = list_voiceprints()
    with base_layout():
        with ui.row().classes("w-full justify-between items-center"):
            ui.label("Speaker voiceprints").classes("text-lg text-dark font-bold")
            enroll_button = ui.button("Enroll new voiceprint", color="dark")
            enroll_button.props("no-caps unelevated icon=record_voice_over")
        ui.separator()

        if not profiles:
            with ui.column().classes("w-full items-center gap-3 py-12"):
                ui.icon("record_voice_over").classes("text-5xl text-grey")
                ui.label("No speaker voiceprints enrolled").classes("text-md text-grey")
        else:
            with ui.list().classes("w-full").props("separator"):
                with ui.item():
                    with ui.grid(columns="1.2fr 0.7fr 0.8fr 1.2fr 0.6fr") as grid:
                        grid.classes("w-full text-grey text-xs items-end")
                        ui.label("Name")
                        ui.label("Dimension")
                        ui.label("Enrollments")
                        ui.label("Last enrolled")
                        ui.label("Actions")
                for profile in profiles:
                    with ui.item().classes("hover:bg-gray-100"):
                        with ui.grid(columns="1.2fr 0.7fr 0.8fr 1.2fr 0.6fr") as grid:
                            grid.classes("w-full items-center gap-x-4")
                            ui.label(profile.name).classes("font-medium")
                            ui.label(str(profile.embedding_dim)).classes("font-light")
                            ui.label(str(len(profile.enrollments))).classes("font-light")
                            ui.label(_last_enrolled(profile.enrollments)).classes(
                                "font-light text-xs"
                            )
                            delete_button = ui.button("Remove", color="gray-100")
                            delete_button.props("no-caps size=0.7rem unelevated text-color=dark")
                            delete_button.on_click(lambda name=profile.name: _confirm_remove(name))

        enroll_button.on_click(
            lambda: enroll_dialog(
                {profile.name for profile in profiles},
                on_success=ui.navigate.reload,
            )
        )


def _last_enrolled(enrollments: list[dict]) -> str:
    if not enrollments:
        return "-"
    return str(enrollments[-1].get("enrolled_at", "-"))


def _confirm_remove(name: str) -> None:
    with ui.dialog(value=True) as dialog, ui.card().classes("p-8 gap-3"):
        dialog.props("persistent")
        ui.label(f"Remove voiceprint {name}?").classes("font-bold text-dark")
        ui.separator()
        with ui.row().classes("w-full justify-end"):
            cancel_button = ui.button("Cancel", color="gray-100")
            cancel_button.props("unelevated no-caps text-color=dark")
            confirm_button = ui.button("Confirm", color="dark")
            confirm_button.props("unelevated no-caps")

    async def remove_and_reload() -> None:
        try:
            await remove_voiceprint_async(name)
            dialog.close()
            ui.navigate.reload()
        except Exception as error:
            dialog.close()
            show_voiceprint_error(error)

    cancel_button.on_click(dialog.close)
    confirm_button.on_click(remove_and_reload)
