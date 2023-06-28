import os
import re
import time
from dataclasses import dataclass

# Rich imports.
from rich.text import Text

# Textual imports.
from textual.containers import Grid
from textual.screen import Screen
from textual.widgets import Button, DataTable, Input, Static

# Local imports.
import util as ut


@dataclass
class BrowserRow:
    index: int
    tagged: bool = False


class BrowserDataTable(DataTable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_keys = []
        self.enter_pressed = False
        self.table_rows = {}

    def add_row(self, *args, **kwargs):
        return super().add_row(Text(args[0]), *args[1:], **kwargs)

    def build_table(self, entries):
        self.table_rows = {}
        for i, item in enumerate(entries):
            if "deleted" not in item.data.keys():
                min, sec = divmod(float(item.original_duration), 60)
                self.table_rows[
                    self.add_row(
                        item.name,
                        item.original_size,
                        item.current_size,
                        item.date.strftime("%Y-%m-%d %H:%M:%S"),
                        item.backups,
                        time.strftime("%H:%M:%S", time.gmtime(float(item.original_duration))),
                        f"{round(min):03}:{round(sec):02}",
                        time.strftime("%H:%M:%S", time.gmtime(float(item.current_duration))),
                    )
                ] = BrowserRow(item.data["index"], tagged=False)
        return self.table_rows

    def cursor_row_key(self):
        row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
        return row_key

    def index_to_row_key(self, index):
        for key, values in self.table_rows.items():
            if values.index == index:
                return key

    def on_key(self, event):
        if event.key == "enter":
            self.enter_pressed = True

    def row_key_to_master_attr(self, row_key, attrstr):
        attr = getattr(self.app.master[self.table_rows[row_key].index], attrstr)
        return attr

    def row_key_to_row_num(self, row_key):
        for i, item in enumerate(self.ordered_rows):
            if item.key == row_key:
                return i
        return -1

    def row_num_to_master_attr(self, row_num, attrstr):
        row_key = self.row_num_to_row_key(row_num)
        attr = getattr(self.app.master[self.table_rows[row_key].index], attrstr)
        return attr

    def row_num_to_master_index(self, row_num):
        row_key = self.row_num_to_row_key(row_num)
        return self.table_rows[row_key].index

    def row_num_to_row_key(self, row: int):
        row_key, _ = self.coordinate_to_cell_key((row, 0))
        return row_key


class FilenameInput(Input):

    BINDINGS = [("escape", "input_cancel", "Cancel")]

    def action_input_cancel(self):
        self.value = ""
        self.insert_text_at_cursor(self.parent.table.row_num_to_master_attr(self.parent.current_hi_row, "name"))
        self.parent.set_focus(self.parent.table)

    def action_submit(self):
        self.master_row = self.parent.table.row_num_to_master_index(self.parent.current_hi_row)
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


class RenameYesNoScreen(Screen):
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
        self.app.uninstall_screen("rename")


class SearchInput(Input):

    BINDINGS = [("escape", "input_cancel", "Cancel")]

    def action_input_cancel(self):
        self.parent.filename_input = FilenameInput()
        self.mount(self.parent.filename_input, after=self.parent.table)
        self.parent.filename_input.insert_text_at_cursor(
            self.parent.table.row_num_to_master_attr(self.parent.current_hi_row, "name")
        )
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

    def action_submit(self):
        self.app.move_target_path = self.value
        self.master_row = self.parent.table.row_num_to_master_index(self.parent.current_hi_row)
        self.current_data = self.app.master[self.master_row]
        self.current_file = os.path.join(self.current_data.path, self.current_data.name)
        self.new_file = os.path.join(self.value, self.current_data.name)
        if os.path.exists(self.new_file):
            self.app.install_screen(TargetPathYesNoScreen(self), "target_path")
            self.app.push_screen("target_path")
        else:
            ut.move_file(self)
            self.action_input_cancel()

    # def on_focus_move_cursor(self):
    #     self.action_cursor_left_word()
    #     self.action_cursor_left()

    # def on_focus(self):
    #     self.call_after_refresh(self.on_focus_move_cursor)


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
