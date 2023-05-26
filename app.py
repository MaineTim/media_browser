import argparse
import os
import pickle

# Textual imports.
from textual.app import App

# Local imports.
import media_library as ml
import util as ut
from info_screen import Info
from main_screen import Main
from search_screen import Search


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
        self.file_browser = args.file_browser
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
        parser.add_argument("-f", action="store_true", default=False, dest="file_browser")
        parser.add_argument("-i", type=str, dest="master_input_path", default="master_filelist")
        parser.add_argument("-o", type=str, dest="master_output_path", required=False)
        parser.add_argument("-n", action="store_true", default=False, dest="no_action")
        parser.add_argument("-t", action="append", dest="translation_list")
        parser.add_argument("-v", action="store_true", default=False, dest="verbose")
        parser.add_argument("-w", type=int, dest="name_width", default=80)
        args = parser.parse_args()
        return args


class Masterfile:
    def __init__(self, mf_path, filebrowser=False):
        self.master = []
        if filebrowser:
            if os.path.exists(mf_path):
                master = ml.create_file_list(mf_path, True)
            else:
                ut.exit_error(f"Path not found: {mf_path}")
        else:
            if os.path.exists(mf_path):
                with open(mf_path, "rb") as f:
                    master = pickle.load(f)
            else:
                ut.exit_error(f"Database file not found: {mf_path}")
        for i, item in enumerate(master):
            item.data["index"] = i
            self.master.append(item)


class Browser(App[None]):

    CSS_PATH = "browser.css"

    TITLE = "Media Browser"

    SCREENS = {
        "main": Main,
        "search": Search,
        "info": Info,
    }

    def on_mount(self) -> None:
        self.yes = False
        self.entries = []
        self.changed = []
        self.current_data = None
        self.args = Getargs()
        master = Masterfile(self.app.args.master_input_path, self.args.file_browser)
        self.master = master.master
        self.push_screen("main")


if __name__ == "__main__":
    Browser().run()
