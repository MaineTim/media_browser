import os

from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

import util as ut


class RenameFileInput(Input):

    BINDINGS = [("escape", "input_cancel", "Cancel")]

    def action_input_cancel(self):
        self.value = ""
        self.insert_text_at_cursor(self.parent.table.row_num_to_master_attr(self.parent.table.cursor_row, "name"))
        self.parent.set_focus(self.parent.table)

    async def action_submit(self):
        self.master_row = self.parent.table.row_num_to_master_index(self.parent.table.cursor_row)
        self.current_data = self.app.master[self.master_row]
        self.current_file = os.path.join(self.current_data.path, self.current_data.name)
        self.new_file = os.path.join(self.current_data.path, self.value)
        if os.path.exists(self.new_file):
            self.app.push_screen(RenameYesNoScreen(self))
        else:
            ut.rename_file(self)
            self.action_input_cancel()

    def on_focus_move_cursor(self):
        self.action_cursor_left_word()
        self.action_cursor_left()

    def on_focus(self):
        self.call_after_refresh(self.on_focus_move_cursor)


class RenameYesNoScreen(ModalScreen):
    def __init__(self, fi):
        super().__init__()
        self.fi = fi

    def compose(self):
        yield Grid(
            Label(f"{self.fi.new_file} already exists, overwrite it?", id="question"),
            Button("Yes", variant="error", id="Yes"),
            Button("No", variant="primary", id="No"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if self.app.args.verbose:
            self.log(event.button.id)
        if event.button.id == "Yes":
            ut.rename_file(self.fi)
        self.app.pop_screen()
