import platform
import subprocess
import time

# Textual imports.
from textual.app import ComposeResult
from textual.coordinate import Coordinate
from textual.screen import Screen
from textual.widgets import ListView, Footer, Header

# Local imports.
import util as ut


class Info(Screen):

    BINDINGS = [
        ("escape", "return_to_main", "Main Screen"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self):
        super(Info, self).__init__()
        self.is_info = True
        self.enter_pressed = False
        self.platform = platform.system()

    def action_return_to_main(self):
        self.app.pop_screen()

    def compose(self) -> ComposeResult:
        yield Header()
        yield ListView(classes="listview")
        yield Footer()

    def on_key(self, event):
        if event.key == "enter":
            self.enter_pressed = True

    def finish_mount(self):
        pass

    def on_mount(self) -> None:
#        self.table.call_after_refresh(self.finish_mount)
        pass

    def on_screen_resume(self):
#        self.table.clear()
#        self.table.call_after_refresh(self.finish_mount)
        pass