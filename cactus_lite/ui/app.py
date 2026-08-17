"""Application controller: window shell, navigation, and long-running actions."""

import threading
import tkinter as tk
from tkinter import messagebox

from cactus_lite.auth import elyby
from cactus_lite.auth.accounts import OFFLINE_ID, AccountStore
from cactus_lite.core.paths import APP_NAME, APP_VERSION, ICON_ICO, ICON_PNG, ensure_mc_dir
from cactus_lite.core.settings import Settings
from cactus_lite.minecraft import launch
from cactus_lite.minecraft.java import find_java
from cactus_lite.minecraft.versions import LOADER_NAMES, VersionCatalog
from cactus_lite.ui import theme
from cactus_lite.ui.images import ImageCache, app_icon
from cactus_lite.ui.pages.changelog import ChangelogPage
from cactus_lite.ui.pages.extra import ExtraPage
from cactus_lite.ui.pages.home import HomePage
from cactus_lite.ui.pages.mods import ModsPage
from cactus_lite.ui.theme import ACCENT, BG, BG2, BG3, FG, MUTED

NAV_ITEMS = (("Главная", "\u2302", "home"),
             ("Дополнительные", "\u2699", "extra"),
             ("Моды", "\u25A3", "mods"))
PROGRESS_THROTTLE = 0.05


class App:
    def __init__(self, root):
        ensure_mc_dir()
        self.root = root
        self.settings = Settings()
        self.accounts = AccountStore()
        self.versions = VersionCatalog()
        self.images = ImageCache()
        self.session = launch.GameSession()
        self._current_version_id = self.settings["version"]

        self.nick_var = tk.StringVar(value=self.settings["nick"])
        self.version_var = tk.StringVar(value=self.settings["version"])
        self.status_var = tk.StringVar()
        self.progress_var = tk.DoubleVar(value=0)

        self._setup_window()
        theme.setup_style()
        self._build_shell()
        self.refresh_versions(select=self.settings["version"])
        self.run_async(self._load_compat, self._compat_loaded)

    # --- window -------------------------------------------------------------

    def _setup_window(self):
        root = self.root
        root.title(APP_NAME)
        root.configure(bg=BG)
        root.geometry("680x600")
        root.minsize(600, 560)
        try:
            root.iconbitmap(ICON_ICO)
        except Exception:
            pass
        self._icon = app_icon(ICON_PNG)
        if self._icon is not None:
            try:
                root.iconphoto(True, self._icon)
            except Exception:
                pass
        root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_width()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_height()) // 2
        self.root.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _build_shell(self):
        base = tk.Frame(self.root, bg=BG)
        base.pack(fill="both", expand=True)

        sidebar = tk.Frame(base, bg=BG2, width=170)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        if self._icon is not None:
            self._logo = self._icon.subsample(4, 4)
            tk.Label(sidebar, image=self._logo, bg=BG2).pack(pady=(12, 6))

        self.nav_buttons = []
        for label, icon, page in NAV_ITEMS:
            self._add_nav(sidebar, f"{icon}  {label}", page)
        tk.Frame(sidebar, bg=BG2).pack(fill="both", expand=True)
        self._add_nav(sidebar, "\u2261  Изменения", "changelog")
        tk.Label(sidebar, text=f"by cactunus {APP_VERSION}", font=theme.font(8), fg=MUTED, bg=BG2)\
            .pack(fill="x", pady=(6, 10))

        container = tk.Frame(base, bg=BG)
        container.pack(side="left", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.pages = {}
        for page_class in (HomePage, ExtraPage, ModsPage, ChangelogPage):
            page = page_class(container, self)
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[page.name] = page
        self.home = self.pages["home"]
        self.show_page("home")
        self._center()

    def _add_nav(self, sidebar, text, page):
        button = tk.Button(sidebar, text=text, anchor="w", padx=14, pady=11, bg=BG2, fg=FG,
                           activebackground=BG3, activeforeground=FG, relief="flat", bd=0,
                           font=theme.font(10), cursor="hand2",
                           command=lambda p=page: self.show_page(p))
        button.pack(fill="x")
        self.nav_buttons.append((button, page))

    def show_page(self, name):
        for button, page in self.nav_buttons:
            button.config(fg=ACCENT if page == name else FG)
        page = self.pages[name]
        page.on_show()
        page.tkraise()

    # --- threading helpers --------------------------------------------------

    def ui(self, fn, *args):
        """Run fn(*args) on the Tk thread."""
        self.root.after(0, lambda: fn(*args))

    def run_async(self, work, done=None):
        """Run `work()` on a thread, then `done(result, error)` on the Tk thread."""
        def job():
            try:
                result, error = work(), None
            except Exception as e:
                result, error = None, e
            if done is not None:
                self.ui(done, result, error)

        threading.Thread(target=job, daemon=True).start()

    def status(self, text):
        self.ui(self.status_var.set, text)

    def log(self, line):
        self.ui(self.home.log, line)

    def show_progress(self, show):
        self.ui(self.home.show_progress, show)

    def progress_callback(self):
        """minecraft-launcher-lib progress callback bound to the UI."""
        last = [0.0]

        def set_progress(value):
            import time
            now = time.time()
            if now - last[0] < PROGRESS_THROTTLE:
                return
            last[0] = now
            self.ui(self.progress_var.set, int(value))

        return {"setStatus": lambda msg: self.status(str(msg)) if msg else None,
                "setProgress": set_progress,
                "setMax": lambda _m: None}

    # --- versions -----------------------------------------------------------

    def _load_compat(self):
        return self.versions.refresh_compat()

    def _compat_loaded(self, changed, _error):
        if changed:
            self.refresh_versions()

    def refresh_versions(self, select=None):
        ids = self.versions.installed_ids()
        loader = self.settings["loader"]
        self.home.version_cb["values"] = [self.versions.label(i, loader) for i in ids]
        current = select or self._current_version_id
        if current not in ids:
            current = ids[0] if ids else ""
        self._current_version_id = current
        self.version_var.set(self.versions.label(current, loader) if current in ids else current)
        if not ids and not self.status_var.get():
            self.status_var.set("Версий нет — нажмите «+»")
        self.home.update_skin_button()

    def current_version(self):
        return self._current_version_id or self.versions.id_from_label(self.version_var.get())

    def select_version_by_index(self, index):
        ids = self.versions.ids
        if 0 <= index < len(ids):
            self._current_version_id = ids[index]

    def install_version(self, version):
        self.status(f"Устанавливаю {version}...")
        self.show_progress(True)

        def work():
            launch.install_version(version, callback=self.progress_callback())

        def done(_result, error):
            self.show_progress(False)
            if error:
                self.status("Ошибка установки.")
                messagebox.showerror(APP_NAME, f"Ошибка установки:\n{error}")
            else:
                self.status(f"{version} установлена.")
            self.refresh_versions(select=version)

        self.run_async(work, done)

    def java_path(self):
        return find_java()[0]

    # --- settings / accounts ------------------------------------------------

    def save_settings(self):
        self.settings.update(nick=self.nick_var.get().strip(), version=self.current_version(),
                             ram=self.home.ram_gb())

    def set_loader(self, loader):
        self.settings["loader"] = loader
        self.save_settings()
        self.refresh_versions()
        if self.pages["mods"].winfo_ismapped():
            self.pages["mods"].on_show()

    def reset_settings(self):
        self.settings.reset()
        self.nick_var.set("")
        self.version_var.set("")
        self.pages["extra"].sync_loader()
        self.home.refresh_ram()
        self.refresh_versions()
        self.status("Настройки сброшены.")

    def select_account(self, account_id):
        self.accounts.select(account_id)
        self.home.refresh_accounts()
        account = self.accounts.selected_account()
        self.status(f"Аккаунт: {account['username']}" if account else "Оффлайн-режим.")

    def add_account(self, profile):
        account = self.accounts.add(profile)
        self.home.refresh_accounts()
        self.status(f"Вход выполнен: {account['username']}")

    def logout_account(self, account):
        self.run_async(lambda: elyby.invalidate(account))
        self.accounts.remove(account["id"])
        self.home.refresh_accounts()
        self.status("Вы вышли из аккаунта Ely.by.")

    # --- launching ----------------------------------------------------------

    def launch(self):
        if self.session.running:
            return
        version = self.current_version()
        if not version:
            messagebox.showinfo(APP_NAME, "Сначала установите версию (кнопка «+»).")
            return
        loader = self.settings["loader"]
        if not self.versions.supports(version, loader):
            messagebox.showwarning(
                APP_NAME, f"{LOADER_NAMES[loader]} не поддерживает эту версию Minecraft.\n\n"
                          "Выберите совместимую версию — несовместимые помечены «(недоступна)».")
            return

        stored = self.accounts.selected_account()
        nick = None
        if stored is None:
            nick = self.home.validate_nick()
            if nick is None:
                return
        self.save_settings()
        ram = self.home.ram_gb()
        self.home.set_running(True)
        note = f" | {LOADER_NAMES[loader]}" if loader != "none" else ""
        who = stored["username"] if stored else nick
        self.log(f"Запуск: {version} | {who} | RAM: {ram} GB{note}")
        self.run_async(lambda: self._launch_worker(version, loader, stored, nick, ram),
                       self._launch_finished)

    def _launch_worker(self, version, loader, stored, nick, ram):
        account, _ = launch.resolve_account(stored, nick)
        if stored is not None and account.get("access_token") != stored.get("access_token"):
            self.ui(self.accounts.update, account)
        self.show_progress(True)
        try:
            command = launch.prepare_command(
                version, loader, account, ram,
                callback=self.progress_callback(), on_status=self.status,
                on_progress=lambda done, total: None)
        finally:
            self.show_progress(False)
        self.status("Запуск игры...")
        self.log("» " + " ".join(command))
        self.session.start(command, on_line=self.log,
                           on_window=lambda: self.ui(self.home.set_close_mode))
        self.session.wait()
        self.status("Игра закрыта.")

    def _launch_finished(self, _result, error):
        self.show_progress(False)
        self.home.set_running(False)
        if error:
            self.status("Ошибка запуска.")
            messagebox.showerror(APP_NAME, f"Ошибка запуска:\n{error}")

    def close_game(self):
        if not self.session.running:
            return
        if not messagebox.askyesno(APP_NAME, "Закрыть игру?"):
            return
        self.status("Закрываю игру...")
        self.run_async(self.session.close)

    def on_close(self):
        if self.session.running and not messagebox.askyesno(
                APP_NAME, "Игра ещё запущена. Закрыть лаунчер?"):
            return
        self.root.destroy()
