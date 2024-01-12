import re

from textual.widgets import Input

import util as ut
from rename_file_input import RenameFileInput


class SearchInput(Input):

    BINDINGS = [("escape", "input_cancel", "Cancel")]

    def __init__(self, search_screen, search_entries):
        super().__init__()
        self.search_screen = search_screen
        self.search_entries = search_entries

    def action_input_cancel(self):
        self.parent.rename_file_input = RenameFileInput()
        self.mount(self.parent.rename_file_input, after=self.parent.table)
        self.parent.rename_file_input.insert_text_at_cursor(
            self.parent.table.row_num_to_master_attr(self.parent.table.cursor_row, "name")
        )
        self.parent.set_focus(self.parent.table)
        self.remove()

    async def action_submit(self):
        self.targets = re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', self.value)
        if self.targets[0][0] == "\\":
            self.search_screen.search_duration, self.search_screen.entries = ut.search_duration(
                self, self.search_entries, self.targets
            )
        else:
            self.search_screen.entries = ut.search_strings(self, self.search_entries, self.targets)
        if self.search_screen.entries != []:
            self.app.push_screen(self.search_screen)
        self.action_input_cancel()


class SearchInputQuote(Input):

    BINDINGS = [("escape", "input_cancel", "Cancel")]

    def __init__(self, search_screen, search_entries):
        super().__init__()
        self.search_screen = search_screen
        self.search_entries = search_entries

    def action_input_cancel(self):
        self.parent.rename_file_input = RenameFileInput()
        self.mount(self.parent.rename_file_input, after=self.parent.table)
        self.parent.rename_file_input.insert_text_at_cursor(
            self.parent.table.row_num_to_master_attr(self.parent.table.cursor_row, "name")
        )
        self.parent.set_focus(self.parent.table)
        self.remove()

    async def action_submit(self):
        self.targets = re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', self.value)
        if self.targets[0][0] == "\\":
            self.search_screen.search_duration, self.search_screen.entries = ut.search_duration(
                self, self.search_entries, self.targets
            )
        else:
            self.search_screen.entries = ut.search_strings(self, self.search_entries, self.targets)
        if self.search_screen.entries != []:
            self.app.push_screen(self.search_screen)
        self.action_input_cancel()

    def on_focus_move_cursor(self):
        self.action_cursor_left_word()
        self.action_cursor_left()

    def on_focus(self):
        self.call_after_refresh(self.on_focus_move_cursor)
