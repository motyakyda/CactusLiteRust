"""Main page: account, nickname, version, RAM and the play button."""

import re
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

from cactus_lite.auth.accounts import OFFLINE_ID
from cactus_lite.core.paths import APP_NAME
from cactus_lite.minecraft import skins
from cactus_lite.minecraft.versions import supports_skin
from cactus_lite.ui import ram as ram_options
from cactus_lite.ui import theme
from cactus_lite.ui.dialogs.account import AccountDialog
from cactus_lite.ui.dialogs.install_version import InstallVersionDialog
from cactus_lite.ui.pages.base import Page
from cactus_lite.ui.theme import ACCENT, BG, BG2, BG3, CONSOLE_BG, CONSOLE_FG, FG, MUTED

NICK_RE = re.compile(r"[A-Za-z0-9_]{1,16}")
RAM_TICK_MS = 5000


class HomePage(Page):
    name = "home"

    def build(self):
        app = self.app
        self.console_shown = False
        self._ram_values = [2]
        self._ram_selectable = {2}
        self._ram_recommended = 2
        self._ram_filling = False
        self._last_ram_label = ""

        theme.section_label(self, "АККАУНТ").pack(anchor="w", padx=20, pady=(20, 5))
        account_row = tk.Frame(self, bg=BG)
        account_row.pack(fill="x", padx=20)
        self.account_var = tk.StringVar()
        self.account_cb = theme.combobox(account_row, self.account_var, size=11)
        self.account_cb.pack(side="left", fill="x", expand=True, ipady=4)
        self.account_cb.bind("<<ComboboxSelected>>", self._on_account_selected)
        theme.ghost_button(account_row, "Ely.by", self._open_account_dialog, size=9)\
            .pack(side="left", padx=(8, 0), ipadx=6, ipady=6)
        self.account_logout_btn = theme.ghost_button(account_row, "Выйти", self._logout,
                                                     size=9, fg=MUTED, active_fg=FG)
        self.account_logout_btn.pack(side="left", padx=(6, 0), ipadx=6, ipady=6)

        self.nick_label = theme.section_label(self, "НИКНЕЙМ")
        self.nick_label.pack(anchor="w", padx=20, pady=(14, 5))
        self.nick_row = tk.Frame(self, bg=BG)
        self.nick_row.pack(fill="x", padx=20)
        nick = theme.entry(self.nick_row, app.nick_var)
        nick.pack(side="left", fill="x", expand=True, ipady=7)
        nick.bind("<Return>", lambda e: app.launch())
        self.skin_btn = theme.ghost_button(self.nick_row, "Скин", self._pick_skin, size=9, width=6)
        self.skin_btn.pack(side="left", padx=(8, 0), ipady=8)

        self.version_label = theme.section_label(self, "ВЕРСИЯ")
        self.version_label.pack(anchor="w", padx=20, pady=(14, 5))
        version_row = tk.Frame(self, bg=BG)
        self.version_row = version_row
        version_row.pack(fill="x", padx=20)
        self.version_cb = theme.combobox(version_row, app.version_var)
        self.version_cb.pack(side="left", fill="x", expand=True, ipady=4)
        self.version_cb.bind("<<ComboboxSelected>>", self._on_version_selected)
        tk.Button(version_row, text="+", font=theme.font(14, "bold"), fg=FG, bg=BG3,
                  activebackground=BG2, activeforeground=ACCENT, relief="flat", bd=0, width=3,
                  cursor="hand2", command=self._open_install_dialog)\
            .pack(side="left", padx=(8, 0), ipady=2)

        theme.section_label(self, "ПАМЯТЬ (GB)").pack(anchor="w", padx=20, pady=(14, 5))
        self.ram_var = tk.StringVar()
        self.ram_cb = theme.combobox(self, self.ram_var, width=18)
        self.ram_cb.pack(anchor="w", padx=20, ipady=4)

        self.launch_btn = theme.primary_button(self, "ИГРАТЬ", app.launch, size=14)
        self.launch_btn.pack(fill="x", padx=20, ipady=10, pady=(18, 0))

        self.progress = ttk.Progressbar(self, variable=app.progress_var, maximum=100)
        self.status_label = tk.Label(self, textvariable=app.status_var, font=theme.font(9),
                                     fg=MUTED, bg=BG, anchor="w", justify="left", wraplength=420)
        self.status_label.pack(fill="x", padx=20, pady=(12, 0))

        self.log_btn = theme.ghost_button(self, "журнал", self.toggle_console, size=8, fg=MUTED,
                                          active_fg=FG)
        self.log_btn.pack(anchor="w", padx=20, pady=(8, 0))
        self.console = tk.Text(self, font=(theme.MONO, 8), bg=CONSOLE_BG, fg=CONSOLE_FG,
                               relief="flat", height=8, state="disabled")

        self.refresh_ram()
        self.ram_var.trace_add("write", self._on_ram_change)
        self.after(RAM_TICK_MS, self._tick_ram)
        self.refresh_accounts()

    # --- accounts -----------------------------------------------------------

    def refresh_accounts(self):
        items = self.app.accounts.labels()
        self._account_ids = [account_id for account_id, _label in items]
        self.account_cb["values"] = [label for _id, label in items]
        selected = self.app.accounts.selected
        if selected not in self._account_ids:
            selected = OFFLINE_ID
        self.account_var.set(dict(items)[selected])
        offline = selected == OFFLINE_ID
        self.account_logout_btn.config(state="disabled" if offline else "normal")
        self._set_nick_visible(offline)
        self.update_skin_button()

    def _set_nick_visible(self, visible):
        if visible:
            self.nick_label.pack(anchor="w", padx=20, pady=(14, 5), before=self.version_label)
            self.nick_row.pack(fill="x", padx=20, before=self.version_label)
        else:
            self.nick_label.pack_forget()
            self.nick_row.pack_forget()

    def _on_account_selected(self, _event=None):
        index = self.account_cb.current()
        if 0 <= index < len(self._account_ids):
            self.app.select_account(self._account_ids[index])

    def _open_account_dialog(self):
        AccountDialog(self.app).show()

    def _logout(self):
        account = self.app.accounts.selected_account()
        if not account:
            return
        if not messagebox.askyesno(APP_NAME, f"Выйти из аккаунта «{account['username']}»?"):
            return
        self.app.logout_account(account)

    # --- version ------------------------------------------------------------

    def _on_version_selected(self, _event=None):
        index = self.version_cb.current()
        self.app.select_version_by_index(index)
        self.update_skin_button()

    def _open_install_dialog(self):
        InstallVersionDialog(self.app).show()

    def update_skin_button(self):
        version = self.app.current_version()
        offline = self.app.accounts.selected == OFFLINE_ID
        if offline and version and supports_skin(version):
            self.skin_btn.pack(side="left", padx=(8, 0), ipady=8)
        else:
            self.skin_btn.pack_forget()

    def _pick_skin(self):
        path = filedialog.askopenfilename(
            title="Выберите скин",
            filetypes=[("Изображения", "*.png *.jpg *.jpeg *.webp *.bmp *.gif"),
                       ("Все файлы", "*.*")])
        if not path:
            return
        try:
            skins.save_skin(path)
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Не удалось обработать изображение:\n{e}")
            return
        self.app.status("Скин выбран — будет подставлен в игру.")

    # --- RAM ----------------------------------------------------------------

    def refresh_ram(self):
        labels, values, selectable, recommended = ram_options.options()
        if labels != list(self.ram_cb["values"]):
            self.ram_cb["values"] = labels
        self._ram_values = values
        self._ram_selectable = selectable
        self._ram_filling = True
        current = ram_options.parse(self.ram_var.get(), values)
        saved = self.app.settings["ram"]
        if current is None and saved in selectable:
            current = saved
        if current is None or current == self._ram_recommended or current not in selectable:
            current = recommended
        self.ram_var.set(ram_options.label_for(current, recommended, selectable))
        self._ram_recommended = recommended
        self._last_ram_label = self.ram_var.get()
        self._ram_filling = False

    def ram_gb(self):
        value = ram_options.parse(self.ram_var.get(), self._ram_values)
        if value is not None:
            return value
        return self._ram_values[0] if self._ram_values else 2

    def _on_ram_change(self, *_args):
        if self._ram_filling:
            return
        value = self.ram_gb()
        if value not in self._ram_selectable:
            self.ram_var.set(self._last_ram_label)
            self.app.status(f"{value} ГБ сейчас заняты системой — выбрать нельзя.")
        else:
            self._last_ram_label = self.ram_var.get()

    def _tick_ram(self):
        try:
            self.refresh_ram()
        except Exception:
            pass
        self.after(RAM_TICK_MS, self._tick_ram)

    # --- launch button / progress / log -------------------------------------

    def set_running(self, running):
        if running:
            self.launch_btn.config(state="disabled", text="ЗАПУСК...")
        else:
            self.launch_btn.config(state="normal", text="ИГРАТЬ", command=self.app.launch)

    def set_close_mode(self):
        self.launch_btn.config(state="normal", text="Закрыть", command=self.app.close_game)

    def show_progress(self, show):
        self.app.progress_var.set(0)
        if show:
            self.progress.pack(fill="x", padx=20, pady=(14, 0), before=self.status_label)
        else:
            self.progress.pack_forget()

    def log(self, line):
        self.console.config(state="normal")
        self.console.insert("end", line + "\n")
        self.console.see("end")
        self.console.config(state="disabled")

    def toggle_console(self):
        if self.console_shown:
            self.console.pack_forget()
        else:
            self.console.pack(fill="both", expand=True, padx=20, pady=(10, 0), before=self.log_btn)
        self.console_shown = not self.console_shown

    def validate_nick(self):
        """Return a valid nickname, or None after showing a warning."""
        nick = self.app.nick_var.get().strip() or "Steve"
        if not NICK_RE.fullmatch(nick):
            messagebox.showwarning(APP_NAME, "Ник: латиница, цифры, «_», до 16 символов.")
            return None
        return nick
