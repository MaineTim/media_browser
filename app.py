import argparse
import os
import pickle

# Textual imports.
from textual.app import App, CSSPathType
from textual.driver import Driver
# Local imports.
import media_library as ml
import util as ut
from info_screen import Info
from main_screen import Main

# from search_screen import Search


class Getargs:
    def __init__(self):
        args = self.get_args()
        self.file_browser = args.file_browser
        self.master_input_path = args.master_input_path
        if not args.master_output_path:
            self.master_output_path = args.master_input_path
        else:
            self.master_output_path = args.master_output_path
        self.name_width = args.name_width if args.name_width else 80
        self.no_action = args.no_action
        self.verbose = args.verbose
        self.write_csv = args.write_csv

    def get_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-d", action="store_true", default=False, dest="write_csv")
        parser.add_argument("-f", action="store_true", default=False, dest="file_browser")
        parser.add_argument("-i", type=str, dest="master_input_path", default="master_filelist")
        parser.add_argument("-o", type=str, dest="master_output_path", required=False)
        parser.add_argument("-n", action="store_true", default=False, dest="no_action")
        parser.add_argument("-v", action="store_true", default=False, dest="verbose")
        parser.add_argument("-w", type=int, dest="name_width", default=80)
        args = parser.parse_args()
        return args


class Masterfile:
    def __init__(self, mf_path, filebrowser=False):
        self.filebrowser = filebrowser
        self.mf_path = mf_path
        self.refresh()

    def refresh(self):
        self.master = []
        if self.filebrowser:
            if os.path.exists(self.mf_path):
                master = ml.create_file_list(self.mf_path, True)
            else:
                ut.exit_error(f"Path not found: {self.mf_path}")
        else:
            if os.path.exists(self.mf_path):
                with open(self.mf_path, "rb") as f:
                    master = pickle.load(f)
            else:
                ut.exit_error(f"Database file not found: {self.mf_path}")
        master.sort(key=lambda x: x.name)
        for i, item in enumerate(master):
            item.data["index"] = i
            self.master.append(item)


class Browser(App):

    CSS_PATH = "browser.css"

    TITLE = "Media Browser"

    SCREENS = {
        "main": Main,
        "info": Info,
    }

    def __init__(
        self, driver_class: type[Driver] | None = None, css_path: CSSPathType | None = None, watch_css: bool = False
    ):
        super().__init__(driver_class, css_path, watch_css)
        self.args = Getargs()
        self.changed = []
        self.current_data = None
        self.file_count = 0
        self.move_target_path = ""
        self.rename_tagged_options = ""
        self.search_terms = ""
        self.search_history = []
        self.search_entry = ""
        self.skip_str = ""
        self.saved_browser_history_filename = ".saved_media_browser_history"
        self.vlc_skiptime = 0

        self.title = f"Media Browser: {self.file_count} files"

        if os.path.exists(self.saved_browser_history_filename):
            with open(self.saved_browser_history_filename, "r") as f:
                self.search_history = [entry.rstrip() for entry in f]

        self.master_instance = Masterfile(self.app.args.master_input_path, self.args.file_browser)
        self.master = self.master_instance.master

    def on_mount(self) -> None:

        self.push_screen("main")

    def master_refresh(self):

        self.master_instance.refresh()
        self.master = self.master_instance.master

    def update_title(self, *, file_count = None, search_terms = None, skip_length = None):

        self.app.file_count = file_count if file_count is not None else self.app.file_count
        self.app.search_terms = search_terms if search_terms is not None else self.app.search_terms
        self.app.vlc_skiptime = skip_length if skip_length is not None else self.app.vlc_skiptime
        self.app.skip_str = "" if self.app.vlc_skiptime == 0 else f" Skip: {str(self.app.vlc_skiptime)} secs."
        self.title = f"Media Browser: {self.app.file_count} files. {self.app.search_terms} {self.app.skip_str}"


if __name__ == "__main__":
    Browser().run()
