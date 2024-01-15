import os

from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label

import media_library as ml
import util as ut
from rename_file_input import RenameFileInput


class WriteMasterfileInput(Input):

    BINDINGS = [("escape", "input_cancel", "Cancel")]

    def action_input_cancel(self):
        self.app.args.master_input_path = self.app.args.master_output_path
        self.value = ""
        self.parent.rename_file_input = RenameFileInput()
        self.mount(self.parent.rename_file_input, after=self.parent.table)
        self.parent.rename_file_input.insert_text_at_cursor(
            self.parent.table.row_num_to_master_attr(self.parent.table.cursor_row, "name")
        )
        self.parent.set_focus(self.parent.table)
        self.remove()

    async def action_submit(self):
        self.app.args.master_output_path = self.value
        if os.path.exists(self.app.args.master_output_path):
            self.app.push_screen(WriteMasterfileYesNoScreen(self), callback=self.do_write)
        else:
            self.write_file()

    def do_write(self, enable: bool) -> None:
        if enable:
            self.write_file()

    def write_file(self):
        if self.app.args.verbose:
            self.log(f"Writing masterfile {self.app.args.master_output_path}")
        ml.write_entries_file(self.app.master, self.app.args.master_output_path, write_csv=True)
        self.action_input_cancel()

    def on_focus_move_cursor(self):
        self.action_cursor_left_word()
        self.action_cursor_left()

    def on_focus(self):
        self.call_after_refresh(self.on_focus_move_cursor)


class WriteMasterfileYesNoScreen(ModalScreen):
    def compose(self):
        yield Grid(
            Label(f"{self.app.args.master_output_path} already exists, overwrite it?", id="question"),
            Button("Yes", variant="error", id="Yes"),
            Button("No", variant="primary", id="No"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> bool:
        if self.app.args.verbose:
            self.log(event.button.id)
        self.dismiss(event.button.id == "Yes")
