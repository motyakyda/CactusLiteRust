"""Shared page base class."""

import tkinter as tk

from cactus_lite.ui.theme import BG


class Page(tk.Frame):
    """A sidebar page. `app` is the controller (cactus_lite.ui.app.App)."""

    name = ""

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.build()

    def build(self):
        raise NotImplementedError

    def on_show(self):
        """Called every time the page becomes visible."""
