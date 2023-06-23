import os
import re

# Textual imports.
from textual.containers import Grid
from textual.screen import Screen
from textual.widgets import Button, DataTable, Input, Static

# Local imports.
import util as ut


class RenameYesNoScreen(Screen):
    def __init__(self, fi):
        super(RenameYesNoScreen, self).__init__()
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
        self.app.uninstall_screen("rename")


class FilenameInput(Input):

    BINDINGS = [("escape", "input_cancel", "Cancel")]

    def action_input_cancel(self):
        self.value = ""
        self.insert_text_at_cursor(self.parent.table.get_row_at(self.parent.current_hi_row)[0])
        self.parent.set_focus(self.parent.table)

    def action_submit(self):
        self.master_row = self.parent.table.get_row_at(self.parent.current_row)[-1]
        self.current_data = self.app.master[self.master_row]
        self.current_file = os.path.join(self.current_data.path, self.current_data.name)
        self.new_file = os.path.join(self.current_data.path, self.value)
        if os.path.exists(self.new_file):
            self.app.install_screen(RenameYesNoScreen(self), "rename")
            self.app.push_screen("rename")
        else:
            ut.rename_file(self)
            self.action_input_cancel()

    def on_focus_move_cursor(self):
        self.action_cursor_left_word()
        self.action_cursor_left()

    def on_focus(self):
        self.call_after_refresh(self.on_focus_move_cursor)


class SearchInput(Input):

    BINDINGS = [("escape", "input_cancel", "Cancel")]

    def action_input_cancel(self):
        self.parent.filename_input = FilenameInput()
        self.mount(self.parent.filename_input, after=self.parent.table)
        self.parent.filename_input.insert_text_at_cursor(self.parent.table.get_row_at(self.parent.current_hi_row)[0])
        self.parent.set_focus(self.parent.table)
        self.remove()

    def action_submit(self):
        self.targets = re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', self.value)
        if self.targets[0][0] == "\\":
            self.app.search_duration, self.app.entries = ut.search_duration(self, self.app.master, self.targets)
        else:
            self.app.entries = ut.search_strings(self, self.app.master, self.targets)
        if self.app.entries != []:
            self.app.new_table = True
            self.app.push_screen("search")
        self.action_input_cancel()


class BrowserDataTable(DataTable):
    def __init__(self, *args, **kwargs):
        super(BrowserDataTable, self).__init__(*args, **kwargs)
        self.enter_pressed = False

    def on_key(self, event):
        if event.key == "enter":
            self.enter_pressed = True

    def cursor_row_key(self):
        row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
        return row_key
