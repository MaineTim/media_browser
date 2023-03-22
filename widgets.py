import re

################################################################################
# Textual imports.
from textual.widgets import Input

################################################################################
# Local imports.
import util as ut


################################################################################
class FilenameInput(Input):
    BINDINGS = [("escape", "input_cancel", "Cancel")]

    def action_input_cancel(self):
        self.value = ""
        self.insert_text_at_cursor(self.parent.table.get_row_at(self.parent.current_hi_row)[0])
        self.parent.set_focus(self.parent.table)

    def action_submit(self):
        ut.rename_file(self.parent, self.value)
        self.action_input_cancel()

    def on_focus_move_cursor(self):
        self.action_cursor_left_word()
        self.action_cursor_left()

    def on_focus(self):
        self.call_after_refresh(self.on_focus_move_cursor)


################################################################################
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
        self.app.entries = ut.search_strings(self, self.app.master, self.targets)
        if self.app.entries != []:
            self.app.push_screen("search")
        self.action_input_cancel()
