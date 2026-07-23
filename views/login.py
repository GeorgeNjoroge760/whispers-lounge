import tkinter as tk
from tkinter import messagebox
from utils.theme import COLORS, FONTS


class StaffSelectView(tk.Frame):
    def __init__(self, parent, auth_controller, on_staff_selected, on_admin_login):
        super().__init__(parent, bg=COLORS["bg_cream"])
        self.auth = auth_controller
        self.on_selected = on_staff_selected
        self.on_admin = on_admin_login
        self._build()

    def _build(self):
        center = tk.Frame(self, bg=COLORS["bg_cream"])
        center.place(relx=0.5, rely=0.45, anchor="center")

        cup_label = tk.Label(center, text="\u2615", font=("Segoe UI", 60), bg=COLORS["bg_cream"], fg=COLORS["accent"])
        cup_label.pack()

        tk.Label(center, text=APP_NAME, font=FONTS["title_green"], bg=COLORS["bg_cream"], fg=COLORS["nav_bg"]).pack(pady=(8, 4))
        tk.Label(center, text="Select attendant to start", font=FONTS["body"], bg=COLORS["bg_cream"], fg=COLORS["text_muted"]).pack(pady=(0, 30))

        staff_frame = tk.Frame(center, bg=COLORS["bg_cream"])
        staff_frame.pack()

        staff_users = self.auth.get_all_staff()
        cols = min(len(staff_users), 3)
        for i, user in enumerate(staff_users):
            row, col = divmod(i, cols)
            btn_frame = tk.Frame(staff_frame, bg=COLORS["bg_cream"])
            btn_frame.grid(row=row, column=col, padx=10, pady=8, sticky="nsew")
            staff_frame.columnconfigure(col, weight=1)

            card = tk.Frame(btn_frame, bg=COLORS["bg_white"], highlightbackground=COLORS["nav_bg"], highlightthickness=2, cursor="hand2", padx=30, pady=20)
            card.pack(fill="both", expand=True, ipadx=10, ipady=5)

            tk.Label(card, text=user["full_name"], font=FONTS["staff_name"], bg=COLORS["bg_white"], fg=COLORS["nav_bg"]).pack()
            role_display = user["role"].capitalize()
            tk.Label(card, text=f"\U0001f464  {role_display}", font=FONTS["small"], bg=COLORS["bg_white"], fg=COLORS["text_muted"]).pack(pady=(4, 0))

            for w in [card] + card.winfo_children():
                w.bind("<Button-1>", lambda e, u=user: self._select(u))

        admin_btn = tk.Button(self, text=f"\U0001f512  Admin Login", font=FONTS["small_bold"], bg=COLORS["bg_cream"], fg=COLORS["nav_bg"], activebackground=COLORS["nav_bg"], activeforeground=COLORS["text_white"], relief="solid", borderwidth=2, cursor="hand2", padx=20, pady=8, command=self.on_admin)
        admin_btn.place(relx=0.5, rely=0.92, anchor="center")
        admin_btn.configure(highlightbackground=COLORS["nav_bg"])

    def _select(self, user):
        self.auth.set_current_user(user)
        self.on_selected()


from config import APP_NAME
