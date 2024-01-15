import os
import shlex
import subprocess

from rich.text import Text

# Textual imports.
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label

# Local imports.
import util as ut
from rename_file_input import RenameFileInput


class RenameTaggedFilesInput(Input):

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
        self.screen_parent = self.parent
        self.app.rename_tagged_options = self.value
        if self.parent.tag_count > 0:
            self.indexes = [
                self.parent.table.table_rows[key].index
                for key in self.parent.table.table_rows.keys()
                if self.parent.table.table_rows[key].tagged
            ]
        else:
            self.action_input_cancel()
        self.app.push_screen(RenameTaggedFilesYesNoScreen(self), callback=self.do_rename)
        self.action_input_cancel()

    def do_rename(self, enable: bool) -> None:
        if enable:
            command = ["/opt/homebrew/bin/rename", "-v", *(shlex.split(self.app.rename_tagged_options))]

            for index in self.indexes:
                current_data = self.app.master[index]
                self.current_file = os.path.join(current_data.path, current_data.name)
                self.current_file_utime = current_data.date.timestamp()
                if self.app.args.verbose:
                    self.log(f"Renaming {self.current_file}.")
                final_command = command[:]
                final_command.append(self.current_file)
                result = subprocess.run(final_command, capture_output=True)
                print(f"do_rename result: {result}")
                if (split_point := result.stderr.find(b"renamed to ")) > 0:
                    new_file_path = result.stderr[split_point + 12 : -2].decode("UTF-8")
                    self.app.master[index].name = os.path.split(new_file_path)[1]
                    self.screen_parent.table.update_cell(
                        self.screen_parent.table.index_to_row_key(index),
                        self.screen_parent.table.column_keys[0],
                        Text(self.app.master[index].name),
                    )
                    self.app.changed.append((index, "R", self.app.master[index].name))
                    self.screen_parent.table.table_rows[self.screen_parent.table.index_to_row_key(index)].tagged = False
                    

class RenameTaggedFilesYesNoScreen(ModalScreen):
    def compose(self):
        yield Grid(
            Label(f"Rename tagged files?", id="question"),
            Button("Yes", variant="error", id="Yes"),
            Button("No", variant="primary", id="No"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> bool:
        if self.app.args.verbose:
            self.log(event.button.id)
        self.dismiss(event.button.id == "Yes")
