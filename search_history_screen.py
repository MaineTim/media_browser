import platform

# Textual imports.
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, OptionList


class SearchHistory(Screen):

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self):
        super().__init__()
        self.is_info = True
        self.enter_pressed = False
        self.platform = platform.system()

    def action_cancel(self):
        self.app.search_entry = ""
        self.parent.pop_screen()

    def compose(self) -> ComposeResult:
        yield Header()
        yield OptionList(classes="search_history_optionlist")
        yield Footer()

    def finish_mount(self):
        for entry in self.app.search_history:
            self.search_history_optionlist.add_option(entry)
        self.search_history_optionlist.action_first()

    def on_option_list_option_selected(self, option):
        self.app.search_entry = option.option.prompt
        self.parent.pop_screen()

    def on_mount(self) -> None:
        self.search_history_optionlist = self.query_one(OptionList)
        self.search_history_optionlist.border_title = "Search History"
        self.finish_mount()

    def on_screen_resume(self):
        self.search_history_optionlist.clear_options()
        self.finish_mount()
