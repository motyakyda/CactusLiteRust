"""Colors, fonts and widget factories — the whole visual language lives here."""

import tkinter as tk
from tkinter import ttk

from cactus_lite.core.platform_utils import IS_MACOS, IS_WINDOWS

BG = "#0f1215"
BG2 = "#1a1f25"
BG3 = "#232a31"
FG = "#e8edf2"
MUTED = "#8b949e"
ACCENT = "#22c55e"
ACCENT_DARK = "#16a34a"
ON_ACCENT = "#06130b"
DANGER = "#f2b8b3"
DANGER_ACTIVE = "#ff6b61"
CONSOLE_BG = "#0a0c0e"
CONSOLE_FG = "#9fb3c8"

if IS_WINDOWS:
    FONT = "Segoe UI"
    MONO = "Consolas"
elif IS_MACOS:
    FONT = "Helvetica Neue"
    MONO = "Menlo"
else:
    FONT = "DejaVu Sans"
    MONO = "DejaVu Sans Mono"


def font(size=10, weight=None):
    return (FONT, size, weight) if weight else (FONT, size)


def setup_style():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TCombobox", fieldbackground=BG2, background=BG2, foreground=FG,
                    arrowcolor=MUTED, bordercolor=BG3, lightcolor=BG3, darkcolor=BG3, padding=5)
    style.map("TCombobox", fieldbackground=[("readonly", BG2)], foreground=[("readonly", FG)],
              selectbackground=[("readonly", BG2)], selectforeground=[("readonly", FG)])
    style.configure("TProgressbar", troughcolor=BG2, background=ACCENT, bordercolor=BG,
                    lightcolor=ACCENT, darkcolor=ACCENT)
    style.configure("Vertical.TScrollbar", background=BG2, troughcolor=BG, bordercolor=BG,
                    arrowcolor=MUTED)
    return style


def section_label(parent, text, bg=BG, size=9, weight=None, fg=MUTED):
    return tk.Label(parent, text=text, font=font(size, weight), fg=fg, bg=bg)


def hint_label(parent, text, bg=BG, justify="left", wraplength=400, size=8, **kwargs):
    return tk.Label(parent, text=text, font=font(size), fg=MUTED, bg=bg, justify=justify,
                    wraplength=wraplength, **kwargs)


def primary_button(parent, text, command, size=12, width=None):
    return tk.Button(parent, text=text, font=font(size, "bold"), fg=ON_ACCENT, bg=ACCENT,
                     activebackground=ACCENT_DARK, activeforeground=ON_ACCENT, relief="flat",
                     bd=0, cursor="hand2", command=command,
                     **({"width": width} if width else {}))


def ghost_button(parent, text, command, bg=BG3, size=10, fg=FG, active_fg=ACCENT, width=None):
    return tk.Button(parent, text=text, font=font(size), fg=fg, bg=bg, activebackground=BG2,
                     activeforeground=active_fg, relief="flat", bd=0, cursor="hand2",
                     command=command, **({"width": width} if width else {}))


def entry(parent, textvariable, size=12, bg=BG2, show=None):
    return tk.Entry(parent, textvariable=textvariable, font=font(size), bg=bg, fg=FG,
                    insertbackground=FG, relief="flat", highlightthickness=1,
                    highlightbackground=BG3, highlightcolor=ACCENT,
                    **({"show": show} if show else {}))


def combobox(parent, textvariable, values=(), size=12, width=None):
    return ttk.Combobox(parent, textvariable=textvariable, values=list(values), state="readonly",
                        font=font(size), **({"width": width} if width else {}))


def bind_wheel(widget, target=None):
    """Mouse-wheel scrolling with the per-platform event names Tk uses."""
    target = target or widget

    def on_wheel(event):
        delta = event.delta
        step = -1 * (delta // 120) if abs(delta) >= 120 else -1 * delta
        target.yview_scroll(int(step) or (-1 if delta > 0 else 1), "units")

    widget.bind("<MouseWheel>", on_wheel)
    widget.bind("<Button-4>", lambda e: target.yview_scroll(-1, "units"))
    widget.bind("<Button-5>", lambda e: target.yview_scroll(1, "units"))
