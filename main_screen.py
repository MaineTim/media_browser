import platform

from rich.text import Text

# Textual imports.
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header
from textual.widgets.data_table import RowDoesNotExist

# Local imports.
import util as ut
from browser_data_table import BrowserDataTable
from rename_file_input import RenameFileInput
from search_history_screen import SearchHistory
from search_input import SearchInput, SearchInputQuote
from search_screen import Search


class Main(Screen):

    BINDINGS = [
        Binding('"', "search_quote", "Quote"),
        Binding("d", "delete_file", "Del"),
        Binding("i", "file_info", "Info"),
        Binding("m", "move_file", "Move"),
        Binding("q", "app.quit", "Quit"),
        Binding("r", "tagged_rename", "taggedRename"),
        Binding("t", "tag", "Tag"),
        Binding("u", "update", "Update"),
        Binding("/", "search", "Search"),
        Binding("ctrl+t", "untag_all", "Untag All", show=False),
        Binding("ctrl+w", "write_masterfile", "Write Masterfile", show=False),
        Binding("?", "search_history", "Search History", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.platform = platform.system()
        self.resume_from_search_history = False
        self.sort_reverse = False
        self.tag_count = 0

    def action_delete_file(self):
        ut.delete_file(self)

    def action_file_info(self):
        ut.action_file_info(self)

    def action_move_file(self):
        ut.action_move_file(self)

    def action_update(self):
        self.app.master_refresh()
        self.use_name_sort()

    def action_search(self):
        self.rename_file_input.remove()
        self.search_input = SearchInput(Search(), self.app.master)
        self.mount(self.search_input, after=self.table)
        self.search_input.insert_text_at_cursor(self.app.search_entry)
        self.set_focus(self.search_input)

    def action_search_history(self):
        self.resume_from_search_history = True
        self.app.push_screen(SearchHistory())

    def action_search_quote(self):
        self.rename_file_input.remove()
        self.search_input = SearchInputQuote(Search(), self.app.master)
        self.mount(self.search_input, after=self.table)
        self.search_input.insert_text_at_cursor('" .mp4"')
        self.set_focus(self.search_input)

    def action_tag(self):
        ut.action_tag(self)

    def action_tagged_rename(self):
        ut.action_tagged_rename(self)

    def action_untag_all(self):
        saved_row = self.table.cursor_row
        if self.tag_count > 0:
            for key in (key for key in self.table.table_rows.keys() if self.table.table_rows[key].tagged):
                self.table.move_cursor(row=self.table.row_key_to_row_num(key))
                ut.action_tag(self)
        self.table.move_cursor(row=saved_row)

    def action_write_masterfile(self):
        ut.action_write_masterfile(self)

    def compose(self) -> ComposeResult:
        columns = [
            ("Name", self.app.args.name_width),
            ("Orig Size", 10),
            ("Curr Size", 10),
            ("Date", 10),
            ("Backups", 2),
            ("Orig Dur", 10),
            ("Orig Min", 10),
            ("Curr Dur", 10),
        ]
        self.table = BrowserDataTable(columns, self.app.master, classes="datatable")
        yield Header()
        yield self.table
        yield RenameFileInput()
        yield Footer()

    def finish_mount(self):
        self.sort_key = self.table.column_keys[0]
        self.set_focus(self.table)

    def on_data_table_header_selected(self, event):
        def richtext_key(key):
            if isinstance(key, Text):
                return str(key)
            else:
                return key

        key = self.table.cursor_row_key()
        if self.sort_key == event.column_key:
            self.sort_reverse = False if self.sort_reverse else True
        else:
            self.sort_reverse = False
        self.table.sort(event.column_key, key=richtext_key, reverse=self.sort_reverse)
        self.sort_key = event.column_key
        self.table.move_cursor(row=self.table.row_key_to_row_num(key))

    def on_data_table_row_highlighted(self, event: DataTable.CellSelected):
        self.rename_file_input.action_delete_left_all()
        self.rename_file_input.insert_text_at_cursor(self.table.row_num_to_master_attr(event.cursor_row, "name"))
        if self.table.p_vlc and self.table.skipview:
            ut.action_run_viewer(self.table, self.app.vlc_skiptime)

    def on_data_table_row_selected(self, event: DataTable.CellSelected):
        if self.table.enter_pressed:
            self.table.enter_pressed = False
            self.set_focus(self.rename_file_input)

    def on_mount(self) -> None:
        self.rename_file_input = self.query_one(RenameFileInput)
        self.table.call_after_refresh(self.finish_mount)

    def on_screen_resume(self):
        if self.resume_from_search_history:
            self.action_search()
            self.resume_from_search_history = False
            self.app.search_entry = ""

        if self.app.changed != []:
            for index, change, data in self.app.changed:
                match change:
                    case "D":
                        try:
                            self.table.remove_row(self.table.index_to_row_key(index))
                        except RowDoesNotExist:
                            ...
                    case "R":
                        self.table.update_cell(
                            self.table.index_to_row_key(index), self.table.column_keys[0], Text(data)
                        )
            self.app.changed = []

    def use_name_sort(self):
        self.table.clear()
        self.table.table_rows = self.table.populate_rows(self.app.master)
        self.rename_file_input = self.query_one(RenameFileInput)
        self.rename_file_input.action_delete_left_all()
        self.rename_file_input.insert_text_at_cursor(self.table.row_num_to_master_attr(0, "name"))
        self.table.call_after_refresh(self.finish_mount)
