import re

from textual.widgets import Input

import util as ut
from filename_input import FilenameInput
from search_screen import Search


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

    async def action_submit(self):
        self.targets = re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', self.value)
        if self.targets[0][0] == "\\":
            search_duration, entries = ut.search_duration(self, self.app.master, self.targets)
        else:
            entries = ut.search_strings(self, self.app.master, self.targets)
        if entries != []:
            search_screen = Search(entries)
            self.app.push_screen(search_screen)
        self.action_input_cancel()


class SearchInputQuote(Input):

    BINDINGS = [("escape", "input_cancel", "Cancel")]

    def action_input_cancel(self):
        self.parent.filename_input = FilenameInput()
        self.mount(self.parent.filename_input, after=self.parent.table)
        self.parent.filename_input.insert_text_at_cursor(
            self.parent.table.row_num_to_master_attr(self.parent.current_hi_row, "name")
        )
        self.parent.set_focus(self.parent.table)
        self.remove()

    async def action_submit(self):
        self.targets = re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', self.value)
        if self.targets[0][0] == "\\":
            self.app.search_duration, self.app.entries = ut.search_duration(self, self.app.master, self.targets)
        else:
            self.app.entries = ut.search_strings(self, self.app.master, self.targets)
        if self.app.entries != []:
            self.app.push_screen("search")
        self.action_input_cancel()

    def on_focus_move_cursor(self):
        self.action_cursor_left_word()
        self.action_cursor_left()

    def on_focus(self):
        self.call_after_refresh(self.on_focus_move_cursor)
