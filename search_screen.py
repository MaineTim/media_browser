import platform

# Textual imports.
from textual.app import ComposeResult
from textual.coordinate import Coordinate
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header

# Local imports.
import util as ut
from browser_data_table import BrowserDataTable
from filename_input import FilenameInput
from search_input import SearchInput, SearchInputQuote


class Search(Screen):

    BINDINGS = [
        ("escape", "return_to_main", "Main Screen"),
        ("space", "run_viewer", "View"),
        ("d", "delete_file", "Del"),
        ("i", "file_info", "Info"),
        ("m", "move_file", "Move"),
        ("q", "quit", "Quit"),
        ("t", "tag", "Tag"),
        ("/", "search", "Search"),
    ]

    def __init__(self):
        super().__init__()
        self.current_hi_row = 0
        self.current_hi_row_key = None
        self.current_row = 0
        self.current_row_key = None
        self.column_keys = []
        self.search_duration = 0.0
        self.entries = []
        self.is_search = True
        self.platform = platform.system()
        self.p_vlc = None
        self.screen_rows = {}
        self.sort_reverses = False
        self.tag_count = 0
        self.vlc_row = None

    def action_delete_file(self):
        ut.delete_file(self)

    def action_file_info(self):
        ut.action_file_info(self)

    def action_move_file(self):
        ut.action_move_file(self)

    def action_return_to_main(self):
        self.app.pop_screen()

    def action_run_viewer(self):
        ut.action_run_viewer(self)

    def action_search(self):
        self.filename_input.remove()
        self.search_input = SearchInput(Search(), self.entries)
        self.mount(self.search_input, after=self.table)
        self.set_focus(self.search_input)

    def action_search_quote(self):
        self.filename_input.remove()
        self.search_input = SearchInputQuote(Search(), self.entries)
        self.mount(self.search_input, after=self.table)
        self.search_input.insert_text_at_cursor('" .mp4"')
        self.set_focus(self.search_input)

    def action_tag(self):
        ut.action_tag(self)

    def compose(self) -> ComposeResult:
        yield Header()
        yield BrowserDataTable(classes="datatable")
        yield FilenameInput()
        yield Footer()

    def finish_mount(self):
        self.sort_key = self.table.column_keys[6]
        self.table.sort(self.sort_key)
        self.current_hi_row_key = self.table.coordinate_to_cell_key((0, 0)).row_key
        self.set_focus(self.table)
        if self.app.search_duration:
            closest_row = ut.closest_row(self)
            self.table.move_cursor(row=closest_row)

    def on_data_table_header_selected(self, event):
        if event.column_key == self.table.column_keys[0]:
            return
        if self.sort_key == event.column_key:
            self.sort_reverse = False if self.sort_reverse else True
        else:
            self.sort_reverse = False
        self.table.sort(event.column_key, reverse=self.sort_reverse)
        self.sort_key = event.column_key
        coord = Coordinate(row=self.table.cursor_row, column=0)
        self.current_hi_row_key = self.table.coordinate_to_cell_key(coord).row_key

    def on_data_table_row_highlighted(self, event: DataTable.CellSelected):
        self.current_hi_row = event.cursor_row
        self.current_hi_row_key = event.row_key
        self.filename_input.action_delete_left_all()
        self.filename_input.insert_text_at_cursor(self.table.row_num_to_master_attr(event.cursor_row, "name"))

    def on_data_table_row_selected(self, event: DataTable.CellSelected):
        if self.table.enter_pressed:
            self.table.enter_pressed = False
            self.set_focus(self.filename_input)
        self.current_row = event.cursor_row
        self.current_row_key = event.row_key
        self.filename_input.action_delete_left_all()
        self.filename_input.insert_text_at_cursor(self.table.row_num_to_master_attr(event.cursor_row, "name"))

    def on_mount(self) -> None:
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
        if self.app.args.verbose:
            self.log(f"{len(self.entries)} records found.")
        self.table = self.query_one(BrowserDataTable)
        self.table.cursor_type = "row"
        for c in columns:
            self.table.column_keys.append(self.table.add_column(c[0], width=c[1]))
        self.screen_rows = self.table.build_table(self.entries)
        self.filename_input = self.query_one(FilenameInput)
        self.filename_input.action_delete_left_all()
        self.filename_input.insert_text_at_cursor(self.table.row_num_to_master_attr(0, "name"))
        self.table.call_after_refresh(self.finish_mount)
