import platform
import subprocess
import time

# Textual imports.
from textual.app import ComposeResult
from textual.coordinate import Coordinate
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header
from textual.widgets.data_table import RowDoesNotExist

# Local imports.
import util as ut
from widgets import FilenameInput


class Search(Screen):

    BINDINGS = [
        ("escape", "return_to_main", "Main Screen"),
        ("space", "run_viewer", "View"),
        ("d", "delete_file", "Del"),
        ("i", "file_info", "Info"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self):
        super(Search, self).__init__()
        self.is_search = True
        self.current_hi_row = 0
        self.current_hi_row_key = None
        self.current_row = 0
        self.current_row_key = None
        self.enter_pressed = False
        self.column_keys = []
        self.platform = platform.system()
        self.p_vlc = None
        self.sort_reverse = False
        self.vlc_row = None

    def action_delete_file(self):
        ut.delete_file(self)

    def action_file_info(self):
        try:
            master_row = self.table.get_row_at(self.current_hi_row)[-1]
        except RowDoesNotExist:
            return
        self.app.current_data = self.app.master[master_row]
        self.app.push_screen("info")

    def action_return_to_main(self):
        self.app.pop_screen()

    def action_run_viewer(self):
        if self.p_vlc:
            ut.kill_vlc(self)
        if self.vlc_row == self.current_hi_row:
            self.vlc_row = None
            return
        self.p_vlc = subprocess.Popen(
            ut.build_command("vlc", ut.get_path(self, self.table.get_row_at(self.current_hi_row)[-1])),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.vlc_row = self.current_hi_row

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(classes="datatable")
        yield FilenameInput()
        yield Footer()

    def on_data_table_header_selected(self, event):
        if self.sort_key == event.column_key:
            self.sort_reverse = False if self.sort_reverse else True
        else:
            self.sort_reverse = False
        self.table.sort(event.column_key, self.column_keys[0], reverse=self.sort_reverse)
        self.sort_key = event.column_key
        coord = Coordinate(row=self.table.cursor_row, column=0)
        self.current_hi_row_key = self.table.coordinate_to_cell_key(coord).row_key

    def on_data_table_row_selected(self, event: DataTable.CellSelected):
        if self.enter_pressed:
            self.enter_pressed = False
            self.set_focus(self.filename_input)
        self.current_row = event.cursor_row
        self.current_row_key = event.row_key
        self.filename_input.action_delete_left_all()
        self.filename_input.insert_text_at_cursor(self.table.get_row_at(event.cursor_row)[0])

    def on_data_table_row_highlighted(self, event: DataTable.CellSelected):
        self.current_hi_row = event.cursor_row
        self.current_hi_row_key = event.row_key
        self.filename_input.action_delete_left_all()
        self.filename_input.insert_text_at_cursor(self.table.get_row_at(event.cursor_row)[0])

    def on_key(self, event):
        if event.key == "enter":
            self.enter_pressed = True

    def finish_mount(self):
        self.sort_key = self.column_keys[6]
        self.table.sort(self.sort_key)
        self.current_hi_row_key = self.table.coordinate_to_cell_key((0, 0)).row_key
        self.set_focus(self.table)
        if self.app.args.translation_list and self.app.args.verbose:
            self.log(self.app.args.translation_list.keys())

    def build_table(self):
        for i, item in enumerate(self.app.entries):
            if "deleted" not in item.data.keys():
                min, sec = divmod(float(item.original_duration), 60)
                self.table.add_row(
                    item.name,
                    item.original_size,
                    item.current_size,
                    item.date.strftime("%Y-%m-%d %H:%M:%S"),
                    item.backups,
                    time.strftime("%H:%M:%S", time.gmtime(float(item.original_duration))),
                    f"{round(min):03}:{round(sec):02}",
                    time.strftime("%H:%M:%S", time.gmtime(float(item.current_duration))),
                    item.data["index"],
                )
        self.filename_input = self.query_one(FilenameInput)
        self.filename_input.action_delete_left_all()
        self.filename_input.insert_text_at_cursor(self.table.get_row_at(0)[0])
        self.table.call_after_refresh(self.finish_mount)

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
            ("Index", 0),
        ]
        if self.app.args.verbose:
            self.log(f"{len(self.app.entries)} records found.")
        self.table = self.query_one(DataTable)
        self.table.cursor_type = "row"
        for c in columns:
            self.column_keys.append(self.table.add_column(c[0], width=c[1]))
        self.build_table()

    def on_screen_resume(self):
        if self.app.new_table:
            self.app.new_table = False
            self.table.clear()
            self.build_table()