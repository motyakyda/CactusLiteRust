"""«Дополнительные»: game folder, resets and the mod loader selector."""

import tkinter as tk
from tkinter import messagebox

from cactus_lite.core.paths import APP_NAME, APP_VERSION, MC_DIR
from cactus_lite.core.platform_utils import open_path
from cactus_lite.minecraft import skins
from cactus_lite.minecraft.versions import LOADER_NAMES, LOADER_UI_IDS, LOADER_UI_VALUES
from cactus_lite.ui import theme
from cactus_lite.ui.pages.base import Page
from cactus_lite.ui.theme import BG, FG, MUTED

LOADER_HINT = ("Не все версии совместимы со всеми подсистемами модов.\n"
               "Буквы рядом с версией: F — Forge, G — Fabric, N — NeoForge.\n"
               "С выбранной подсистемой несовместимые версии помечены «(недоступна)».")
RAM_HINT = ("ОЗУ определяется автоматически. Пометка «заняты» — этой памяти\n"
            "сейчас не хватает, её выбрать нельзя.")


class ExtraPage(Page):
    name = "extra"

    def build(self):
        theme.section_label(self, "НАСТРОЙКИ").pack(anchor="w", padx=20, pady=(20, 10))

        theme.section_label(self, "Папка игры:").pack(anchor="w", padx=20)
        tk.Label(self, text=MC_DIR, font=theme.font(9), fg=FG, bg=BG, justify="left",
                 wraplength=400).pack(anchor="w", padx=20, pady=(4, 0))

        for text, command, fg in (
            ("Открыть папку игры", lambda: open_path(MC_DIR), FG),
            ("Сбросить настройки", self._reset_settings, MUTED),
            ("Сбросить скин", self._reset_skin, MUTED),
        ):
            theme.ghost_button(self, text, command, fg=fg, active_fg=FG)\
                .pack(anchor="w", padx=20, ipadx=10, ipady=5, pady=(8, 0))

        theme.section_label(self, "ПОДСИСТЕМА МОДОВ").pack(anchor="w", padx=20, pady=(18, 5))
        self.loader_var = tk.StringVar()
        self.loader_cb = theme.combobox(self, self.loader_var, values=LOADER_UI_VALUES, size=11)
        self.loader_cb.pack(anchor="w", padx=20, ipady=4)
        self.loader_cb.bind("<<ComboboxSelected>>", self._on_loader_change)
        self.sync_loader()

        theme.hint_label(self, LOADER_HINT).pack(anchor="w", padx=20, pady=(10, 0))
        theme.hint_label(self, RAM_HINT).pack(anchor="w", padx=20, pady=(16, 0))
        theme.hint_label(self, f"by cactunus {APP_VERSION}", wraplength=200)\
            .pack(side="bottom", pady=12)

    def sync_loader(self):
        loader = self.app.settings["loader"]
        index = LOADER_UI_IDS.index(loader) if loader in LOADER_UI_IDS else 0
        self.loader_cb.current(index)

    def _on_loader_change(self, _event=None):
        index = self.loader_cb.current()
        loader = LOADER_UI_IDS[index] if 0 <= index < len(LOADER_UI_IDS) else "none"
        self.app.set_loader(loader)
        if loader != "none":
            self.app.status(f"Подсистема: {LOADER_NAMES.get(loader, loader)}")

    def _reset_settings(self):
        if messagebox.askyesno(APP_NAME, "Сбросить настройки?"):
            self.app.reset_settings()

    def _reset_skin(self):
        if not messagebox.askyesno(APP_NAME, "Убрать скин?"):
            return
        skins.remove_skin()
        self.app.status("Скин убран.")
