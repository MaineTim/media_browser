import platform

from rich.text import Text

# Textual imports.
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header
from textual.widgets.data_table import RowDoesNotExist

# Local imports.
import util as ut
from browser_data_table import BrowserDataTable
from filename_input import FilenameInput
from search_input import SearchInput, SearchInputQuote
from search_screen import Search


class Main(Screen):

    BINDINGS = [
        ('"', "search_quote", "Quote"),
        ("space", "run_viewer", "View"),
        ("d", "delete_file", "Del"),
        ("i", "file_info", "Info"),
        ("m", "move_file", "Move"),
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("t", "tag", "Tag"),
        ("/", "search", "Search"),
    ]

    def __init__(self):
        super().__init__()
        self.platform = platform.system()
        self.p_vlc = None
        self.sort_reverse = False
        self.tag_count = 0
        self.vlc_row = None

    def action_delete_file(self):
        ut.delete_file(self)

    def action_file_info(self):
        ut.action_file_info(self)

    def action_move_file(self):
        ut.action_move_file(self)

    def action_refresh(self):
        self.app.master_refresh()
        self.use_name_sort()

    def action_run_viewer(self):
        ut.action_run_viewer(self)

    def action_search(self):
        self.filename_input.remove()
        self.search_input = SearchInput(Search(), self.app.master)
        self.mount(self.search_input, after=self.table)
        self.set_focus(self.search_input)

    def action_search_quote(self):
        self.filename_input.remove()
        self.search_input = SearchInputQuote(Search(), self.app.master)
        self.mount(self.search_input, after=self.table)
        self.search_input.insert_text_at_cursor('" .mp4"')
        self.set_focus(self.search_input)

    def action_tag(self):
        ut.action_tag(self)

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
        yield FilenameInput()
        yield Footer()

    def finish_mount(self):
        self.sort_key = self.table.column_keys[0]
        self.set_focus(self.table)

    def on_data_table_header_selected(self, event):
        key = self.table.cursor_row_key()
        if event.column_key == self.table.column_keys[0]:
            self.use_name_sort()
            self.sort_key = self.table.column_keys[0]
        else:
            if self.sort_key == event.column_key:
                self.sort_reverse = False if self.sort_reverse else True
            else:
                self.sort_reverse = False
            self.table.sort(event.column_key, reverse=self.sort_reverse)
            self.sort_key = event.column_key
        self.table.move_cursor(row=self.table.row_key_to_row_num(key))

    def on_data_table_row_highlighted(self, event: DataTable.CellSelected):
        self.filename_input.action_delete_left_all()
        self.filename_input.insert_text_at_cursor(self.table.row_num_to_master_attr(event.cursor_row, "name"))

    def on_data_table_row_selected(self, event: DataTable.CellSelected):
        if self.table.enter_pressed:
            self.table.enter_pressed = False
            self.set_focus(self.filename_input)

    def on_mount(self) -> None:
        self.filename_input = self.query_one(FilenameInput)
        self.table.call_after_refresh(self.finish_mount)

    def on_screen_resume(self):
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
        self.filename_input = self.query_one(FilenameInput)
        self.filename_input.action_delete_left_all()
        self.filename_input.insert_text_at_cursor(self.table.row_num_to_master_attr(0, "name"))
        self.table.call_after_refresh(self.finish_mount)
