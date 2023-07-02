import os

# Textual imports.
from textual.containers import Grid
from textual.screen import Screen
from textual.widgets import Button, Input, Static

# Local imports.
import util as ut
from filename_input import FilenameInput


class TargetPathInput(Input):

    BINDINGS = [("escape", "input_cancel", "Cancel")]

    def action_input_cancel(self):
        self.value = ""
        self.parent.filename_input = FilenameInput()
        self.mount(self.parent.filename_input, after=self.parent.table)
        self.parent.filename_input.insert_text_at_cursor(
            self.parent.table.row_num_to_master_attr(self.parent.current_hi_row, "name")
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
            indexes = [self.parent.table.row_num_to_master_index(self.parent.current_hi_row)]
        for index in indexes:
            current_data = self.app.master[index]
            self.current_file = os.path.join(current_data.path, current_data.name)
            self.new_file = os.path.join(self.value, current_data.name)
            if os.path.exists(self.new_file):
                self.app.install_screen(TargetPathYesNoScreen(self), "target_path")
                self.app.push_screen("target_path")
            else:
                ut.move_file(self)
        self.action_input_cancel()


class TargetPathYesNoScreen(Screen):
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
        self.app.uninstall_screen("target_path")
