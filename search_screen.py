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
from widgets import FilenameInput


################################################################################
class Search(Screen):
    """The main application screen."""

    BINDINGS = [
        ("space", "run_viewer", "View"),
        ("q", "quit", "Quit"),
        ("s", "search", "Search"),
    ]

    def __init__(self):
        super(Search, self).__init__()
        self.current_hi_row = 0
        self.current_row = 0
        self.enter_pressed = False
        self.column_keys = []
        self.platform = platform.system()
        self.p_vlc = None
        self.sort_reverse = False
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
            ("Name", self.app.args.name_width),
            ("Orig Size", 10),
            ("Curr Size", 10),
            ("Date", 10),
            ("Backups", 2),
            ("Orig Dur", 10),
            ("Curr Dur", 10),
            ("Index", 0),
        ]
        self.log(f"{len(self.app.entries)} records found.")
        self.table = self.query_one(DataTable)
        self.table.cursor_type = "row"
        for c in columns:
            self.column_keys.append(self.table.add_column(c[0], width=c[1]))
        for i, item in enumerate(self.app.entries):
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
        if self.app.args.translation_list:
            self.log(self.app.args.translation_list.keys())
