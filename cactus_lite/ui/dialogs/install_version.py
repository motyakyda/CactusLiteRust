"""Version installation dialog."""

import tkinter as tk

from cactus_lite.minecraft.versions import available_versions, sort_key
from cactus_lite.ui import theme
from cactus_lite.ui.dialogs.base import Dialog
from cactus_lite.ui.theme import BG, BG2, FG, MUTED


class InstallVersionDialog(Dialog):
    title = "Установка версии"
    size = (420, 330)

    def build(self):
        win = self.win
        self._all = []
        self._ids = []

        theme.section_label(win, "Версия").pack(anchor="w", padx=18, pady=(18, 5))
        self.var = tk.StringVar()
        self.combo = theme.combobox(win, self.var)
        self.combo.pack(fill="x", padx=18, ipady=4)

        self.only_release = tk.BooleanVar(value=True)
        tk.Checkbutton(win, text="только стабильные релизы", variable=self.only_release, bg=BG,
                       fg=FG, activebackground=BG, activeforeground=FG, selectcolor=BG2,
                       font=theme.font(9), cursor="hand2")\
            .pack(anchor="w", padx=18, pady=(10, 0))
        self.only_release.trace_add("write", lambda *a: self._apply_filter())

        self.info = tk.Label(win, text="Загружаю список версий...", font=theme.font(9), fg=MUTED,
                             bg=BG, anchor="w")
        self.info.pack(fill="x", padx=18, pady=(10, 0))

        self.install_btn = theme.primary_button(win, "УСТАНОВИТЬ", self._install)
        self.install_btn.config(state="disabled")
        self.install_btn.pack(fill="x", padx=18, ipady=8, pady=(16, 0))

        self.app.run_async(available_versions, self._loaded)

    def _loaded(self, versions, error):
        if not self.alive():
            return
        if error:
            self.info.config(text=f"Ошибка загрузки: {error}")
            return
        self._all = versions
        self._apply_filter()
        self.info.config(text=f"Доступно версий: {len(versions)}")
        self.install_btn.config(state="normal")

    def _apply_filter(self):
        if not self.alive():
            return
        items = [(i, t) for i, t in self._all
                 if not self.only_release.get() or t == "release"]
        items.sort(key=lambda x: sort_key(x[0]), reverse=True)
        self._ids = [i for i, _t in items]
        labels = [self.app.versions.label(i, self.app.settings["loader"]) for i in self._ids]
        self.combo["values"] = labels
        if labels:
            self.var.set(labels[0])

    def _install(self):
        label = self.var.get()
        if not label:
            return
        index = self.combo.current()
        version = self._ids[index] if 0 <= index < len(self._ids) else \
            self.app.versions.id_from_label(label)
        self.close()
        self.app.install_version(version)
