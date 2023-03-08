"""Main application class for the app."""

##############################################################################
# Textual imports.
from textual.app import App

##############################################################################
# Local imports.
from main_screen import Main


##############################################################################
class Browser(App[None]):
    """The main application class."""

    CSS_PATH = "browser.css"
    """The name of the CSS file for the application."""

    TITLE = "Media Browser"
    """The title of the application."""

    #    SUB_TITLE = f"v{__version__}"
    #    """The sub-title of the application."""

    SCREENS = {"main": Main}
    """The collection of application screens."""

    def on_mount(self) -> None:
        """Set up the application on startup."""
        self.push_screen("main")


##############################################################################
def run() -> None:
    """Run the application."""
    Browser().run()
