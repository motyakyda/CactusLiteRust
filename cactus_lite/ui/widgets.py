"""Reusable composite widgets: scroll area, mod tile, drop zone."""

import os
import tkinter as tk

from cactus_lite.ui import theme
from cactus_lite.ui.theme import ACCENT, BG, BG2, BG3, FG, MUTED

try:
    from tkinterdnd2 import DND_FILES
    DND_AVAILABLE = True
except Exception:
    DND_FILES = None
    DND_AVAILABLE = False


class ScrollFrame(tk.Frame):
    """A vertically scrollable container; add children to `.body`."""

    def __init__(self, parent, bg=BG):
        super().__init__(parent, bg=bg)
        canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview, bg=BG2,
                                 activebackground=BG3, troughcolor=bg, bd=0,
                                 highlightthickness=0)
        canvas.configure(yscrollcommand=scrollbar.set)
        self.body = tk.Frame(canvas, bg=bg)
        window = canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window, width=e.width))
        theme.bind_wheel(canvas)
        theme.bind_wheel(self.body, canvas)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        self.canvas = canvas


class ModTile(tk.Frame):
    """Catalog/search tile: avatar, name, note, version picker and action button."""

    WIDTH = 176
    HEIGHT = 168

    def __init__(self, parent, mod, photo, on_install, values=(), selected=None):
        super().__init__(parent, bg=BG2, highlightthickness=1, highlightbackground=BG3,
                         width=self.WIDTH, height=self.HEIGHT)
        self.grid_propagate(False)
        self.pack_propagate(False)
        self.mod = mod

        avatar = tk.Canvas(self, width=44, height=44, bg=BG2, highlightthickness=0)
        avatar.pack(pady=(12, 4))
        if photo is not None:
            avatar.create_image(22, 22, image=photo)
        else:
            color = mod.get("color", ACCENT)
            avatar.create_rectangle(2, 2, 42, 42, fill=color, outline=color)
            avatar.create_text(22, 22, text=(mod["name"][:1] or "?"), fill="#ffffff",
                               font=theme.font(16, "bold"))

        tk.Label(self, text=mod["name"][:16], font=theme.font(10, "bold"), fg=FG, bg=BG2).pack()
        tk.Label(self, text=mod.get("note") or " ", font=theme.font(7), fg=MUTED, bg=BG2,
                 wraplength=160, justify="center").pack(pady=(1, 6))

        bottom = tk.Frame(self, bg=BG2)
        bottom.pack(fill="x", padx=10, pady=(0, 10))
        self.var = tk.StringVar()
        self.combo = theme.combobox(bottom, self.var, values=values, size=8, width=9)
        self.combo.pack(side="left")
        if values:
            self.var.set(selected or values[0])
        else:
            self.combo.config(state="disabled")
        self.button = theme.primary_button(bottom, "УСТАНОВИТЬ", on_install, size=8, width=9)
        self.button.pack(side="right")

    def busy(self, text="..."):
        self.button.config(state="disabled", text=text)

    def progress(self, text):
        self.button.config(text=text)

    def done(self, command):
        self.button.config(state="normal", text="ГОТОВО", command=command)

    def reset(self):
        self.button.config(state="normal", text="УСТАНОВИТЬ")


class DropZone(tk.Frame):
    """Click-or-drag target for adding mod files manually."""

    def __init__(self, parent, on_files, status_var, hint_var):
        super().__init__(parent, bg=BG2, highlightthickness=2, highlightbackground=BG3)
        self.on_files = on_files

        icon = tk.Canvas(self, width=64, height=78, bg=BG2, highlightthickness=0)
        icon.pack(pady=(22, 6))
        icon.create_rectangle(14, 8, 50, 66, fill=BG3, outline=FG, width=2)
        icon.create_polygon(32, 8, 50, 8, 50, 26, fill=BG3, outline=FG, width=2)
        for y, x2 in ((38, 44), (46, 44), (54, 36)):
            icon.create_line(20, y, x2, y, fill=MUTED, width=2)

        tk.Label(self, text="Здесь вы можете загрузить свои файлы", font=theme.font(12),
                 fg=FG, bg=BG2).pack(pady=(8, 4))
        tk.Label(self, textvariable=hint_var, font=theme.font(9), fg=MUTED, bg=BG2)\
            .pack(pady=(0, 18))
        tk.Label(self, textvariable=status_var, font=theme.font(9), fg=ACCENT, bg=BG2)\
            .pack(pady=(0, 12))
        theme.primary_button(self, "ЗАГРУЗИТЬ ВРУЧНУЮ", lambda: on_files(None), size=9)\
            .pack(pady=(0, 16), ipadx=12, ipady=5)

        hint_var.set("Перетащите сюда файл мода (например, .jar)" if DND_AVAILABLE
                     else "Нажмите на блок или кнопку ниже, чтобы выбрать файл")

        for widget in (self, icon):
            widget.config(cursor="hand2")
            widget.bind("<Button-1>", lambda e: on_files(None))
        if DND_AVAILABLE:
            self._register_dnd([self, icon] + list(self.winfo_children()))

    def _register_dnd(self, widgets):
        for widget in widgets:
            try:
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<Drop>>", self._on_drop)
                widget.dnd_bind("<<DragEnter>>", lambda e: self.highlight(True))
                widget.dnd_bind("<<DragLeave>>", lambda e: self.highlight(False))
            except Exception:
                pass

    def highlight(self, on):
        self.config(highlightbackground=ACCENT if on else BG3)

    def _on_drop(self, event):
        self.highlight(False)
        paths = [p for p in self.tk.splitlist(event.data) if os.path.exists(p)]
        if paths:
            self.on_files(paths)
