from flaskwebgui import FlaskUI
from typing import List
from dataclasses import dataclass

@dataclass
class CustomUI(FlaskUI):
    #Add custom_flags option to class
    custom_flags: List[str] = None
    def get_browser_command(self):
        flags = [
            self.browser_path,
            f"--user-data-dir={self.profile_dir}",
            "--new-window",
            "--no-first-run",
        ]

        if self.width and self.height:
            flags.extend([f"--window-size={self.width},{self.height}"])
        elif self.fullscreen:
            flags.extend(["--start-maximized"])

        if self.custom_flags:
            flags.extend(self.custom_flags)

        flags.extend([f"--app={self.url}"])
        return flags