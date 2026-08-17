"""«Изменения»: rendered version history."""

import tkinter as tk

from cactus_lite.ui import theme
from cactus_lite.ui.changelog_data import CHANGELOG
from cactus_lite.ui.pages.base import Page
from cactus_lite.ui.theme import ACCENT, BG, BG2, BG3, FG, MUTED


class ChangelogPage(Page):
    name = "changelog"

    def build(self):
        theme.section_label(self, "ИЗМЕНЕНИЯ").pack(anchor="w", padx=20, pady=(20, 8))

        wrap = tk.Frame(self, bg=BG)
        wrap.pack(fill="both", expand=True, padx=(20, 12), pady=(0, 16))
        text = tk.Text(wrap, bg=BG, fg=FG, font=theme.font(9), relief="flat", bd=0, wrap="word",
                       state="disabled", cursor="arrow")
        scrollbar = tk.Scrollbar(wrap, command=text.yview, bg=BG2, activebackground=BG3,
                                 troughcolor=BG, bd=0, highlightthickness=0)
        text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)

        text.tag_configure("ver", foreground=ACCENT, font=theme.font(12, "bold"))
        text.tag_configure("sub", foreground=MUTED, font=theme.font(9, "bold"))
        text.tag_configure("item", foreground=FG, lmargin1=14, lmargin2=14)
        text.tag_configure("gap", font=theme.font(4))

        text.config(state="normal")
        for entry in CHANGELOG:
            text.insert("end", entry["version"] + "\n", "ver")
            for title, items in (("Исправления", entry["fixes"]), ("Добавлено", entry["features"])):
                if not items:
                    continue
                text.insert("end", title + "\n", "sub")
                for item in items:
                    text.insert("end", "• " + item + "\n", "item")
            text.insert("end", "\n", "gap")
        text.config(state="disabled")
        theme.bind_wheel(text)
