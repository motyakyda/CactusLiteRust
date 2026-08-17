"""Entry point: `python launcher.py` or `python -m cactus_lite`."""

import tkinter as tk

from cactus_lite.core.paths import ensure_mc_dir
from cactus_lite.core.platform_utils import hide_console
from cactus_lite.ui.app import App

try:
    from tkinterdnd2 import TkinterDnD
    _ROOT_FACTORY = TkinterDnD.Tk
except Exception:
    _ROOT_FACTORY = tk.Tk


def main():
    hide_console()
    ensure_mc_dir()
    root = _ROOT_FACTORY()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
