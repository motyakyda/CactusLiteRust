"""Modal dialog base: centered, transient, dark themed."""

import tkinter as tk

from cactus_lite.ui.theme import BG


class Dialog:
    title = ""
    size = (420, 330)

    def __init__(self, app):
        self.app = app
        self.win = None

    def show(self):
        root = self.app.root
        self.win = tk.Toplevel(root)
        self.win.title(self.title)
        self.win.configure(bg=BG)
        self.win.transient(root)
        self.win.resizable(False, False)
        width, height = self.size
        self.win.geometry(f"{width}x{height}")
        self.win.update_idletasks()
        x = root.winfo_rootx() + (root.winfo_width() - width) // 2
        y = root.winfo_rooty() + (root.winfo_height() - height) // 2
        self.win.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.win.bind("<Escape>", lambda e: self.close())
        self.build()
        return self.win

    def build(self):
        raise NotImplementedError

    def close(self):
        if self.win is not None:
            self.win.destroy()
            self.win = None

    def alive(self):
        return self.win is not None and self.win.winfo_exists()
