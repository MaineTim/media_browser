import os

# Textual imports.
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static

# Local imports.
import util as ut
from rename_file_input import RenameFileInput


class MoveFilesInput(Input):

    BINDINGS = [("escape", "input_cancel", "Cancel")]

    def action_input_cancel(self):
        self.value = ""
        self.parent.rename_file_input = RenameFileInput()
        self.mount(self.parent.rename_file_input, after=self.parent.table)
        self.parent.rename_file_input.insert_text_at_cursor(
            self.parent.table.row_num_to_master_attr(self.parent.table.cursor_row, "name")
        )
        self.parent.set_focus(self.parent.table)
        self.remove()

    async def action_submit(self):
        self.app.move_target_path = self.value
        if self.parent.tag_count > 0:
            indexes = [
                self.parent.table.table_rows[key].index
                for key in self.parent.table.table_rows.keys()
                if self.parent.table.table_rows[key].tagged
            ]
        else:
            indexes = [self.parent.table.row_num_to_master_index(self.parent.table.cursor_row)]
        for index in indexes:
            current_data = self.app.master[index]
            self.current_file = os.path.join(current_data.path, current_data.name)
            self.current_file_utime = current_data.date.timestamp()
            self.new_file = os.path.join(self.value, current_data.name)
            if os.path.exists(self.new_file):
                self.app.push_screen(MoveFilesYesNoScreen(self))
            else:
                ut.move_file(self)
        self.action_input_cancel()


class MoveFilesYesNoScreen(ModalScreen):
    def __init__(self, fi):
        super().__init__()
        self.fi = fi

    def compose(self):
        yield Grid(
            Static(f"{self.fi.new_file} already exists, overwrite it?", id="question"),
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
