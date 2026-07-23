import tkinter as tk
from tkinter import messagebox
from utils.theme import COLORS, FONTS


class AdminLoginView(tk.Frame):
    def __init__(self, parent, auth_controller, on_login_success, on_back):
        super().__init__(parent, bg=COLORS["bg_cream"])
        self.auth = auth_controller
        self.on_success = on_login_success
        self.on_back = on_back
        self._build()

    def _build(self):
        center = tk.Frame(self, bg=COLORS["bg_cream"])
        center.place(relx=0.5, rely=0.5, anchor="center")

        card = tk.Frame(center, bg=COLORS["bg_white"], padx=40, pady=35, highlightbackground=COLORS["border"], highlightthickness=1)
        card.pack()

        tk.Label(card, text="\u2615", font=("Segoe UI", 40), bg=COLORS["bg_white"], fg=COLORS["accent"]).pack()
        tk.Label(card, text=APP_NAME, font=FONTS["title_green"], bg=COLORS["bg_white"], fg=COLORS["nav_bg"]).pack(pady=(4, 2))
        tk.Label(card, text="Admin Login", font=FONTS["small"], bg=COLORS["bg_white"], fg=COLORS["text_muted"]).pack(pady=(0, 25))

        tk.Label(card, text="Username", font=FONTS["small_bold"], bg=COLORS["bg_white"], fg=COLORS["text_primary"], anchor="w").pack(fill="x")
        self.username_entry = tk.Entry(card, font=FONTS["body"], bg=COLORS["bg_primary"], fg=COLORS["text_primary"], insertbackground=COLORS["text_primary"], relief="flat", highlightthickness=1, highlightbackground=COLORS["border"], width=30)
        self.username_entry.pack(pady=(2, 15), ipady=6, fill="x")
        self.username_entry.focus_set()

        tk.Label(card, text="Password", font=FONTS["small_bold"], bg=COLORS["bg_white"], fg=COLORS["text_primary"], anchor="w").pack(fill="x")
        self.password_entry = tk.Entry(card, font=FONTS["body"], bg=COLORS["bg_primary"], fg=COLORS["text_primary"], insertbackground=COLORS["text_primary"], relief="flat", highlightthickness=1, highlightbackground=COLORS["border"], show="*", width=30)
        self.password_entry.pack(pady=(2, 20), ipady=6, fill="x")
        self.password_entry.bind("<Return>", lambda e: self._login())

        tk.Button(card, text="Login", font=FONTS["heading"], bg=COLORS["nav_bg"], fg=COLORS["text_white"], activebackground="#14532d", activeforeground=COLORS["text_white"], relief="flat", cursor="hand2", command=self._login).pack(fill="x", ipady=8)

        self.status_label = tk.Label(card, text="", font=FONTS["small"], bg=COLORS["bg_white"], fg=COLORS["danger"])
        self.status_label.pack(pady=(12, 0))

        tk.Button(card, text="\u2190 Back to staff selection", font=FONTS["small"], bg=COLORS["bg_white"], fg=COLORS["text_muted"], relief="flat", cursor="hand2", command=self.on_back).pack(pady=(15, 0))

    def _login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            self.status_label.config(text="Please enter username and password")
            return
        success, msg = self.auth.login(username, password)
        if success:
            self.on_success()
        else:
            self.status_label.config(text=msg)
            self.password_entry.delete(0, tk.END)


from config import APP_NAME
