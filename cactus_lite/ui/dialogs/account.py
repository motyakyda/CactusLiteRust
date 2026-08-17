"""Ely.by sign-in dialog.

The password is only held in the entry widget for the duration of the request:
Ely.by returns tokens, and only tokens are saved to disk.
"""

import tkinter as tk
import webbrowser

from cactus_lite.auth import elyby
from cactus_lite.ui import theme
from cactus_lite.ui.dialogs.base import Dialog
from cactus_lite.ui.theme import ACCENT, BG, FG, MUTED

REGISTER_URL = "https://account.ely.by/register"
INTRO = ("Войдите в аккаунт Ely.by, чтобы играть с ником, скином и плащом\n"
         "на серверах с online-mode. Пароль не сохраняется — лаунчер хранит\n"
         "только токен доступа.")


class AccountDialog(Dialog):
    title = "Вход через Ely.by"
    size = (430, 400)

    def build(self):
        win = self.win
        self._busy = False
        self._client_token = elyby.new_client_token()

        theme.section_label(win, "ELY.BY").pack(anchor="w", padx=18, pady=(18, 4))
        theme.hint_label(win, INTRO, wraplength=380).pack(anchor="w", padx=18)

        self.login_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.totp_var = tk.StringVar()

        theme.section_label(win, "E-mail или ник").pack(anchor="w", padx=18, pady=(14, 4))
        login_entry = theme.entry(win, self.login_var, size=11)
        login_entry.pack(fill="x", padx=18, ipady=6)

        theme.section_label(win, "Пароль").pack(anchor="w", padx=18, pady=(10, 4))
        password_entry = theme.entry(win, self.password_var, size=11, show="•")
        password_entry.pack(fill="x", padx=18, ipady=6)
        password_entry.bind("<Return>", lambda e: self._submit())

        self.totp_label = theme.section_label(win, "Код двухфакторной аутентификации")
        self.totp_entry = theme.entry(win, self.totp_var, size=11)
        self.totp_entry.bind("<Return>", lambda e: self._submit())

        self.status_var = tk.StringVar()
        self.status = tk.Label(win, textvariable=self.status_var, font=theme.font(9), fg=ACCENT,
                               bg=BG, anchor="w", justify="left", wraplength=380)
        self.status.pack(fill="x", padx=18, pady=(10, 0))

        self.submit_btn = theme.primary_button(win, "ВОЙТИ", self._submit)
        self.submit_btn.pack(fill="x", padx=18, ipady=8, pady=(10, 0))
        theme.ghost_button(win, "Создать аккаунт на ely.by",
                          lambda: webbrowser.open(REGISTER_URL), size=9, fg=MUTED, active_fg=FG)\
            .pack(anchor="w", padx=18, pady=(10, 0), ipadx=8, ipady=4)

        login_entry.focus_set()

    def _show_totp(self):
        if not self.totp_label.winfo_ismapped():
            self.totp_label.pack(anchor="w", padx=18, pady=(10, 4), before=self.status)
            self.totp_entry.pack(fill="x", padx=18, ipady=6, before=self.status)
        self.totp_entry.focus_set()

    def _set_busy(self, busy, message=""):
        self._busy = busy
        self.submit_btn.config(state="disabled" if busy else "normal",
                               text="ВХОД..." if busy else "ВОЙТИ")
        self.status.config(fg=ACCENT)
        self.status_var.set(message)

    def _submit(self):
        if self._busy:
            return
        login = self.login_var.get().strip()
        password = self.password_var.get()
        totp = self.totp_var.get().strip()
        if not login or not password:
            self.status.config(fg="#f2b8b3")
            self.status_var.set("Введите логин и пароль.")
            return
        self._set_busy(True, "Проверяю данные...")

        def work():
            return elyby.authenticate(login, password, totp=totp or None,
                                      client_token=self._client_token)

        self.app.run_async(work, self._done)

    def _done(self, profile, error):
        if not self.alive():
            return
        if isinstance(error, elyby.TwoFactorRequired):
            self._set_busy(False)
            self.status.config(fg=FG)
            self.status_var.set("Введите код из приложения аутентификации.")
            self._show_totp()
            return
        if error:
            self._set_busy(False)
            self.status.config(fg="#f2b8b3")
            self.status_var.set(str(error))
            return
        self.password_var.set("")
        self.close()
        self.app.add_account(profile)
