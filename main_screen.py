import platform
import subprocess

# Textual imports.
from textual.app import ComposeResult
from textual.coordinate import Coordinate
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header
from textual.widgets.data_table import RowDoesNotExist

# Local imports.
import util as ut
from widgets import BrowserDataTable, FilenameInput, SearchInput


class Main(Screen):

    BINDINGS = [
        ("space", "run_viewer", "View"),
        ("d", "delete_file", "Del"),
        ("i", "file_info", "Info"),
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("/", "search", "Search"),
    ]

    def __init__(self):
        super().__init__()

        self.is_search = False
        self.current_hi_row = 0
        self.current_hi_row_key = None
        self.current_row = 0
        self.current_row_key = None
        self.platform = platform.system()
        self.p_vlc = None
        self.sort_reverse = False
        self.vlc_row = None

    def action_delete_file(self):
        ut.delete_file(self)

    def action_file_info(self):
        try:
            master_row = self.table.row_num_to_master_index(self.current_hi_row)
        except RowDoesNotExist:
            return
        self.app.current_data = self.app.master[master_row]
        self.app.push_screen("info")

    def action_refresh(self):
        self.app.master_instance.refresh()
        self.use_name_sort()

    def action_run_viewer(self):
        if self.p_vlc:
            ut.kill_vlc(self)
        if self.vlc_row == self.current_hi_row:
            self.vlc_row = None
            return
        self.p_vlc = subprocess.Popen(
            ut.build_command("vlc", ut.get_path(self, self.table.row_num_to_master_index(self.current_hi_row))),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.vlc_row = self.current_hi_row

    def action_search(self):
        self.filename_input.remove()
        self.search_input = SearchInput()
        self.mount(self.search_input, after=self.table)
        self.set_focus(self.search_input)

    def compose(self) -> ComposeResult:
        yield Header()
        yield BrowserDataTable(classes="datatable")
        yield FilenameInput()
        yield Footer()

    def finish_mount(self):
        self.sort_key = self.table.column_keys[0]
        self.current_hi_row_key = self.table.coordinate_to_cell_key((0, 0)).row_key
        self.set_focus(self.table)
        if self.app.args.translation_list and self.app.args.verbose:
            self.log(self.app.args.translation_list.keys())

    def on_data_table_header_selected(self, event):
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
            self.log(f"{len(self.app.master)} records found.")
        self.table = self.query_one(BrowserDataTable)
        self.table.cursor_type = "row"
        for c in columns:
            self.table.column_keys.append(self.table.add_column(c[0], width=c[1]))
        self.app.main_rows = self.table.build_table(self.app.master)
        self.filename_input = self.query_one(FilenameInput)
        self.filename_input.action_delete_left_all()
        self.filename_input.insert_text_at_cursor(self.table.row_num_to_master_attr(0, "name"))
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
                        self.table.update_cell(self.table.index_to_row_key(index), self.table.column_keys[0], data)
            self.app.changed = []

    def use_name_sort(self):
        self.table.clear()
        self.app.main_rows = self.table.build_table(self.app.master)
        self.filename_input = self.query_one(FilenameInput)
        self.filename_input.action_delete_left_all()
        self.filename_input.insert_text_at_cursor(self.table.row_num_to_master_attr(0, "name"))
        self.table.call_after_refresh(self.finish_mount)
