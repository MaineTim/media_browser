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
        self.app.entries = ut.search_strings(self.app.master, self.value)
        self.app.push_screen("search")
        self.action_input_cancel()
