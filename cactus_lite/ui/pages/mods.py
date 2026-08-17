"""«Моды»: manual upload, pinned catalog, Modrinth search, installed list."""

import os
import tkinter as tk
from tkinter import filedialog, messagebox

from cactus_lite.core.paths import APP_NAME, APP_VERSION
from cactus_lite.core.platform_utils import open_path
from cactus_lite.mods import catalog, installer
from cactus_lite.ui import theme
from cactus_lite.ui.pages.base import Page
from cactus_lite.ui.theme import ACCENT, BG, BG3, DANGER, DANGER_ACTIVE, FG, MUTED
from cactus_lite.ui.widgets import DropZone, ModTile, ScrollFrame

TILE_COLUMNS = 2
CATALOG_HINT = ("Sodium — нужен Fabric. OptiFine — для Forge или ванили.\n"
                "Скачанный мод автоматически попадёт в папку mods.")
MANUAL_HINT = ("Мы не ручаемся за ошибки при таком переносе, если мод не подойдёт\n"
               "под подсистему модов или если он скачан не на ту версию.")


def _mb(done, total):
    if total:
        return f"{done / 1048576:.1f}/{total / 1048576:.1f} МБ"
    return f"{done / 1048576:.1f} МБ"


def _fmt_size(n):
    if not n:
        return ""
    if n >= 1024 * 1024:
        return f"{n / 1048576:.1f} МБ"
    return f"{n / 1024:.0f} КБ"


class ModsPage(Page):
    name = "mods"

    def build(self):
        self._catalog_data = {}
        self._catalog_loading = False
        self._search_loading = False
        self._catalog_tiles = {}
        self._search_tiles = {}
        self._search_results = []

        theme.section_label(self, "МОДЫ").pack(anchor="w", padx=20, pady=(20, 10))
        self._build_empty_state()
        self._build_content()

    # --- layout -------------------------------------------------------------

    def _build_empty_state(self):
        self.empty = tk.Frame(self, bg=BG)
        tk.Label(self.empty, text="Нет подсистемы модов", font=theme.font(13, "bold"),
                 fg=FG, bg=BG).pack(pady=(90, 6))
        theme.hint_label(self.empty,
                         "Выберите Forge, Fabric или NeoForge в «Дополнительных»,\n"
                         "чтобы устанавливать моды.", justify="center", size=9).pack()
        theme.ghost_button(self.empty, "Открыть «Дополнительные»",
                           lambda: self.app.show_page("extra"))\
            .pack(pady=(16, 0), ipadx=10, ipady=5)

    def _build_content(self):
        self.content = ScrollFrame(self)
        body = self.content.body

        self.upload_status_var = tk.StringVar()
        self.upload_hint_var = tk.StringVar()
        self.drop_zone = DropZone(body, self._add_local_mods, self.upload_status_var,
                                  self.upload_hint_var)
        self.drop_zone.pack(fill="x", padx=20, pady=(14, 0))
        theme.hint_label(body, MANUAL_HINT, justify="center").pack(pady=(12, 0))

        self.catalog_state_var = tk.StringVar(value="Каталог загружается...")
        theme.section_label(body, "КАТАЛОГ МОДОВ", fg=FG, weight="bold")\
            .pack(anchor="w", padx=20, pady=(20, 2))
        theme.hint_label(body, CATALOG_HINT).pack(anchor="w", padx=20)
        tk.Label(body, textvariable=self.catalog_state_var, font=theme.font(8), fg=ACCENT, bg=BG)\
            .pack(anchor="w", padx=20, pady=(6, 0))
        self.catalog_grid = tk.Frame(body, bg=BG)
        self.catalog_grid.pack(fill="x", padx=12, pady=(2, 0))

        theme.section_label(body, "ПОИСК МОДОВ НА MODRINTH", fg=FG, weight="bold")\
            .pack(anchor="w", padx=20, pady=(20, 2))
        search_row = tk.Frame(body, bg=BG)
        search_row.pack(fill="x", padx=20, pady=(2, 0))
        self.search_var = tk.StringVar()
        search_entry = theme.entry(search_row, self.search_var, size=9, bg=BG3)
        search_entry.pack(side="left", fill="x", expand=True, ipady=5, ipadx=6)
        search_entry.bind("<Return>", lambda e: self._search())
        theme.primary_button(search_row, "НАЙТИ", self._search, size=9)\
            .pack(side="left", padx=(8, 0), ipadx=10, ipady=5)
        self.search_status_var = tk.StringVar()
        tk.Label(body, textvariable=self.search_status_var, font=theme.font(8), fg=ACCENT, bg=BG)\
            .pack(anchor="w", padx=20, pady=(6, 0))
        self.search_grid = tk.Frame(body, bg=BG)
        self.search_grid.pack(fill="x", padx=12, pady=(2, 0))

        self.installed_header_var = tk.StringVar(value="УСТАНОВЛЕННЫЕ МОДЫ")
        tk.Label(body, textvariable=self.installed_header_var, font=theme.font(9, "bold"),
                 fg=FG, bg=BG).pack(anchor="w", padx=20, pady=(16, 4))
        self.installed_list = tk.Frame(body, bg=BG)
        self.installed_list.pack(fill="x", padx=20)
        theme.ghost_button(body, "Открыть папку mods", self._open_mods_dir, size=9)\
            .pack(anchor="w", padx=20, pady=(10, 0), ipadx=8, ipady=4)
        theme.hint_label(body, f"by cactunus {APP_VERSION}", justify="center").pack(pady=(12, 12))

    def on_show(self):
        if self.app.settings["loader"] == "none":
            self.content.pack_forget()
            self.empty.pack(fill="both", expand=True)
            return
        self.empty.pack_forget()
        self.content.pack(fill="both", expand=True)
        self.refresh_installed()
        self._load_catalog()

    def mods_dir(self):
        return installer.mods_dir(self.app.current_version(), self.app.settings["loader"])

    # --- manual upload ------------------------------------------------------

    def _add_local_mods(self, paths):
        if paths is None:
            paths = filedialog.askopenfilenames(
                title="Выберите моды",
                filetypes=[("Файлы модов", "*.jar *.zip"), ("Все файлы", "*.*")])
        for path in paths or []:
            self._add_local_mod(path)

    def _add_local_mod(self, src):
        name = os.path.basename(src)
        if os.path.isdir(src):
            messagebox.showinfo(APP_NAME, "Перетащите файл мода, а не папку.")
            return
        if os.path.splitext(src)[1].lower() not in installer.MOD_EXTENSIONS:
            messagebox.showwarning(APP_NAME,
                                   "Моды обычно бывают файлами .jar.\nВыберите файл .jar или .zip.")
            return
        directory = self.mods_dir()
        if os.path.isfile(os.path.join(directory, name)) and not messagebox.askyesno(
                APP_NAME, f"«{name}» уже есть в папке модов.\nЗаменить его?"):
            return
        self.upload_status_var.set("Мод загружается в папку...")

        def work():
            installer.copy_local_mod(src, directory)

        def done(_result, error):
            if error:
                self.upload_status_var.set("Ошибка загрузки мода.")
                messagebox.showerror(APP_NAME, f"Не удалось скопировать файл:\n{error}")
                return
            self.upload_status_var.set(f"Мод загружен: {name}")
            self.app.status(f"Мод загружен: {name}")
            self.refresh_installed()

        self.app.run_async(work, done)

    # --- pinned catalog -----------------------------------------------------

    def _load_catalog(self):
        if self._catalog_loading:
            return
        cached = catalog.load_cache()
        if cached is not None:
            self._catalog_data = cached
            self._rebuild_catalog()
            return
        self._catalog_loading = True
        self.catalog_state_var.set("Каталог загружается...")

        def work():
            data = catalog.fetch_catalog()
            catalog.save_cache(data)
            return data

        def done(data, error):
            self._catalog_loading = False
            if error:
                self.catalog_state_var.set("Не удалось загрузить каталог. Проверьте интернет.")
                return
            self._catalog_data = data
            self._rebuild_catalog()

        self.app.run_async(work, done)

    def _rebuild_catalog(self):
        for widget in self.catalog_grid.winfo_children():
            widget.destroy()
        self._catalog_tiles = {}
        current_series = catalog.series_of(self.app.current_version())
        shown = 0
        for mod in catalog.PINNED_MODS:
            versions = self._catalog_data.get(mod["id"]) or {}
            if not versions:
                continue
            keys = sorted(versions, key=catalog.version_sort_key, reverse=True)
            labels = [k + (" (рекомендовано)" if catalog.matches_series(k, current_series) else "")
                      for k in keys]
            selected = next((labels[i] for i, k in enumerate(keys)
                             if catalog.matches_series(k, current_series)), None)
            tile = ModTile(self.catalog_grid, mod, self.app.images.mod_icon(mod.get("icon_key")),
                           lambda mid=mod["id"]: self._install_catalog_mod(mid),
                           values=labels, selected=selected)
            tile.grid(row=shown // TILE_COLUMNS, column=shown % TILE_COLUMNS, padx=8,
                      pady=(10, 0), sticky="n")
            tile.keys = keys
            self._catalog_tiles[mod["id"]] = tile
            shown += 1
        self.catalog_state_var.set("" if shown else "Каталог пуст или не загрузился.")

    def _install_catalog_mod(self, mod_id):
        tile = self._catalog_tiles.get(mod_id)
        if tile is None:
            return
        label = tile.var.get()
        if not label:
            messagebox.showinfo(APP_NAME, "Для этой версии мод недоступен.")
            return
        series = label.split(" (")[0]
        info = (self._catalog_data.get(mod_id) or {}).get(series)
        if not info:
            return
        dst = installer.target_path(mod_id, info, self.mods_dir())
        if os.path.isfile(dst) and not messagebox.askyesno(
                APP_NAME, f"«{os.path.basename(dst)}» уже есть в папке модов.\nЗаменить его?"):
            return
        tile.busy("0.0 МБ")

        def work():
            java = self.app.java_path() if mod_id == "optifine" else None
            return installer.install_from_catalog(
                mod_id, series, info, dst, java=java,
                on_progress=lambda done, total: self.app.ui(tile.progress, _mb(done, total)),
                on_stage=lambda text: self.app.ui(tile.progress, text))

        self.app.run_async(work, lambda result, error: self._tile_done(tile, error))

    # --- search -------------------------------------------------------------

    def _search(self):
        query = self.search_var.get().strip()
        if not query or self._search_loading:
            return
        self._search_loading = True
        self.search_status_var.set("Поиск...")
        loader = self.app.settings["loader"]
        loader = loader if loader != "none" else None

        def work():
            return catalog.search_modrinth_mods(query, loader=loader)

        def done(results, error):
            self._search_loading = False
            self._rebuild_search([] if error else results)

        self.app.run_async(work, done)

    def _rebuild_search(self, results):
        for widget in self.search_grid.winfo_children():
            widget.destroy()
        self._search_tiles = {}
        if not results:
            self.search_status_var.set("Ничего не найдено.")
            return
        self.search_status_var.set(f"Найдено: {len(results)}")
        for i, mod in enumerate(results):
            tile = ModTile(self.search_grid, mod, self.app.images.remote_icon(mod.get("icon_url")),
                           lambda m=mod: self._install_search_mod(m))
            tile.grid(row=i // TILE_COLUMNS, column=i % TILE_COLUMNS, padx=8, pady=(10, 0),
                      sticky="n")
            self._search_tiles[mod["id"]] = tile

    def _install_search_mod(self, mod):
        tile = self._search_tiles.get(mod["id"])
        if tile is None:
            return
        tile.busy()
        directory = self.mods_dir()
        version = self.app.current_version()

        def work():
            return installer.install_from_search(
                mod, version, directory,
                on_progress=lambda done, total: self.app.ui(tile.progress, _mb(done, total)))

        self.app.run_async(work, lambda result, error: self._tile_done(tile, error))

    def _tile_done(self, tile, error):
        if error:
            tile.reset()
            messagebox.showerror(APP_NAME, f"Ошибка установки:\n{error}")
            return
        tile.done(self._open_mods_dir)
        self.refresh_installed()
        self.app.status(f"Мод установлен: {tile.mod['name']}")

    # --- installed ----------------------------------------------------------

    def refresh_installed(self):
        for widget in self.installed_list.winfo_children():
            widget.destroy()
        directory = self.mods_dir()
        mods = installer.list_mods(directory)
        self.installed_header_var.set(f"УСТАНОВЛЕННЫЕ МОДЫ ({len(mods)})")
        if not mods:
            tk.Label(self.installed_list, text="Пока пусто — моды появятся здесь после установки.",
                     font=theme.font(9), fg=MUTED, bg=BG, anchor="w").pack(fill="x", pady=(2, 0))
            return
        for name in mods:
            row = tk.Frame(self.installed_list, bg=BG)
            row.pack(fill="x", pady=3)
            path = os.path.join(directory, name)
            size = _fmt_size(os.path.getsize(path)) if os.path.isfile(path) else ""
            tk.Label(row, text=name + (f"  ({size})" if size else ""), font=theme.font(9),
                     fg=FG, bg=BG, anchor="w").pack(side="left", fill="x", expand=True)
            theme.ghost_button(row, "Удалить", lambda n=name: self._remove(n), size=8,
                               fg=DANGER, active_fg=DANGER_ACTIVE).pack(side="right")

    def _remove(self, name):
        if not messagebox.askyesno(APP_NAME, f"Удалить мод «{name}»?"):
            return
        try:
            installer.remove_mod(self.mods_dir(), name)
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Не удалось удалить:\n{e}")
            return
        self.refresh_installed()
        self.app.status(f"Мод удалён: {name}")

    def _open_mods_dir(self):
        directory = self.mods_dir()
        try:
            os.makedirs(directory, exist_ok=True)
            open_path(directory)
        except Exception as e:
            messagebox.showerror(APP_NAME, str(e))
