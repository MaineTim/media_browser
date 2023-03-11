"""Provides the main screen for the application."""

################################################################################
# Python imports.
import argparse
import os
import pickle
import platform
import subprocess
import time

################################################################################
# Textual imports.
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header

################################################################################
# Local imports.
import util as ut
from widgets import FilenameInput, SearchInput


################################################################################
class Getargs:
    def __init__(self):
        args = self.get_args()
        self.write_csv = args.write_csv
        self.master_input_path = args.master_input_path
        if not args.master_output_path:
            self.master_output_path = args.master_input_path
        else:
            self.master_output_path = args.master_output_path
        self.verbose = args.verbose
        self.no_action = args.no_action
        self.name_width = args.name_width if args.name_width else 80
        if args.translation_list:
            self.translation_list = {}
            for i in args.translation_list:
                path, drive = i.split("=")
                self.translation_list[path] = drive
        else:
            self.translation_list = None

    def get_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-d", action="store_true", default=False, dest="write_csv")
        parser.add_argument("-i", type=str, dest="master_input_path", default="master_filelist")
        parser.add_argument("-o", type=str, dest="master_output_path", required=False)
        parser.add_argument("-n", action="store_true", default=False, dest="no_action")
        parser.add_argument("-t", action="append", dest="translation_list")
        parser.add_argument("-v", action="store_true", default=False, dest="verbose")
        parser.add_argument("-w", type=int, dest="name_width", default=80)
        args = parser.parse_args()
        return args


################################################################################
class Masterfile:
    def __init__(self, mf_path):
        if os.path.exists(mf_path):
            with open(mf_path, "rb") as f:
                self.master = pickle.load(f)
        else:
            ut.exit_error(f"Database file not found: {mf_path}")


################################################################################
class Main(Screen):
    """The main application screen."""

    BINDINGS = [
        ("space", "run_viewer", "View"),
        ("d", "delete_file", "Del"),
        ("q", "quit", "Quit"),
        ("s", "search", "Search"),
    ]

    def __init__(self):
        super(Main, self).__init__()
        self.args = Getargs()
        self.current_hi_row = 0
        self.current_row = 0
        self.enter_pressed = False
        self.column_keys = []
        self.platform = platform.system()
        self.p_vlc = None
        self.vlc_row = None

    def action_delete_file(self):
        ut.delete_file(self)

    def action_run_viewer(self):
        if self.p_vlc:
            ut.kill_vlc(self)
        if self.vlc_row == self.current_hi_row:
            self.vlc_row = None
            return

        self.p_vlc = subprocess.Popen(
            ut.build_command("vlc", ut.get_path(self, self.table.get_row_at(self.current_hi_row)[7])),
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

    def on_data_table_row_selected(self, event: DataTable.CellSelected):
        if self.current_row == event.cursor_row or self.enter_pressed:
            self.enter_pressed = False
            self.set_focus(self.filename_input)
        self.current_row = event.cursor_row
        self.filename_input.action_delete_left_all()
        self.filename_input.insert_text_at_cursor(self.table.get_row_at(event.cursor_row)[0])

    def on_data_table_row_highlighted(self, event: DataTable.CellSelected):
        self.current_hi_row = event.cursor_row
        self.filename_input.action_delete_left_all()
        self.filename_input.insert_text_at_cursor(self.table.get_row_at(event.cursor_row)[0])

    def on_filename_input_submitted(self, event):
        ut.rename_file(self, event.input.value)

    def on_key(self, event):
        if event.key == "enter":
            self.enter_pressed = True

    def on_mount(self) -> None:
        columns = [
            ("Name", self.args.name_width),
            ("Orig Size", 10),
            ("Curr Size", 10),
            ("Date", 10),
            ("Backups", 2),
            ("Orig Dur", 10),
            ("Curr Dur", 10),
            ("Index", 0),
        ]
        master = Masterfile(self.args.master_input_path)
        self.master = master.master
        self.log(f"{len(self.master)} records found.")
        self.table = self.query_one(DataTable)
        self.table.cursor_type = "row"
        for c in columns:
            self.column_keys.append(self.table.add_column(c[0], width=c[1]))
        for i, item in enumerate(self.master):
            self.table.add_row(
                item.name,
                item.original_size,
                item.current_size,
                item.date.strftime("%Y-%m-%d %H:%M:%S"),
                item.backups,
                time.strftime("%H:%M:%S", time.gmtime(float(item.original_duration))),
                time.strftime("%H:%M:%S", time.gmtime(float(item.current_duration))),
                i,
            )
        self.sort_key = self.column_keys[0]
        self.table.sort(self.sort_key)
        self.filename_input = self.query_one(FilenameInput)
        self.filename_input.action_delete_left_all()
        self.filename_input.insert_text_at_cursor(self.table.get_row_at(0)[0])
        self.set_focus(self.table)
        if self.args.translation_list:
            self.log(self.args.translation_list.keys())
