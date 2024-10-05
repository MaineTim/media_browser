import platform

# Textual imports.
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, ListItem, ListView


class Info(Screen):

    BINDINGS = [
        (Binding("escape, space", "return_to_main", "Main Screen", key_display="ESC/SPACE")),
        ("q", "app.quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.is_info = True
        self.enter_pressed = False
        self.platform = platform.system()

    def action_return_to_main(self):
        self.app.pop_screen()

    def compose(self) -> ComposeResult:
        yield Header()
        yield ListView(classes="listview")
        yield Footer()

    def finish_mount(self):
        self.listview.append(ListItem(Label("File Info", classes="infoitem")))
        self.listview.append(ListItem(Label(f"UID: {self.app.current_data.UID}", classes="infoitem")))
        self.listview.append(ListItem(Label(f"Path: {self.app.current_data.path}", classes="infoitem")))
        self.listview.append(ListItem(Label(f"Name: {self.app.current_data.name}", classes="infoitem")))
        self.listview.append(
            ListItem(Label(f"Original size: {self.app.current_data.original_size}", classes="infoitem"))
        )
        self.listview.append(ListItem(Label(f"Current size: {self.app.current_data.current_size}", classes="infoitem")))
        self.listview.append(ListItem(Label(f"Date: {self.app.current_data.date}", classes="infoitem")))
        self.listview.append(ListItem(Label(f"Backups: {self.app.current_data.backups}", classes="infoitem")))
        self.listview.append(ListItem(Label(f"Backup paths: {self.app.current_data.paths}", classes="infoitem")))
        self.listview.append(
            ListItem(Label(f"Original Duration: {self.app.current_data.original_duration}", classes="infoitem"))
        )
        self.listview.append(
            ListItem(Label(f"Current Duration: {self.app.current_data.current_duration}", classes="infoitem"))
        )
        self.listview.append(ListItem(Label(f"Inode: {self.app.current_data.ino}", classes="infoitem")))
        self.listview.append(ListItem(Label(f"Number of links: {self.app.current_data.nlink}", classes="infoitem")))
        self.listview.append(ListItem(Label(f"Checksum: {self.app.current_data.csum}", classes="infoitem")))
        self.listview.append(ListItem(Label(f"Data: {self.app.current_data.data}", classes="infoitem")))

    def on_mount(self) -> None:
        self.listview = self.query_one(ListView)
        self.finish_mount()

    def on_screen_resume(self):
        self.listview.clear()
        self.finish_mount()
