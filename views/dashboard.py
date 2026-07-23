import tkinter as tk
from tkinter import messagebox
from utils.theme import COLORS, FONTS, SIZES


class DashboardView(tk.Frame):
    def __init__(self, parent, auth_controller, report_controller, navigate_callback):
        super().__init__(parent, bg=COLORS["bg_primary"])
        self.auth = auth_controller
        self.reports = report_controller
        self.navigate = navigate_callback
        self._build()

    def _build(self):
        nav = tk.Frame(self, bg=COLORS["nav_bg"], height=SIZES["navbar_height"])
        nav.pack(fill="x")
        nav.pack_propagate(False)

        user = self.auth.get_current_user()
        tk.Label(nav, text=f"\u2615  {APP_NAME}", font=FONTS["navbar"], bg=COLORS["nav_bg"], fg=COLORS["text_white"]).pack(side="left", padx=15)
        tk.Label(nav, text=f"Admin Panel", font=FONTS["small"], bg=COLORS["nav_bg"], fg=COLORS["text_white"]).pack(side="left", padx=10)

        right_nav = tk.Frame(nav, bg=COLORS["nav_bg"])
        right_nav.pack(side="right", padx=15)
        tk.Label(right_nav, text=f"\U0001f464 {user['full_name']}", font=FONTS["small"], bg=COLORS["nav_bg"], fg=COLORS["text_white"]).pack(side="left", padx=(0, 10))
        tk.Button(right_nav, text="\u2190 Logout", font=FONTS["small"], bg=COLORS["danger"], fg=COLORS["text_white"], relief="flat", cursor="hand2", padx=12, pady=4, command=self._logout).pack(side="left")

        content = tk.Frame(self, bg=COLORS["bg_primary"])
        content.pack(fill="both", expand=True, padx=20, pady=20)

        summary = self.reports.get_today_summary()

        stats_row = tk.Frame(content, bg=COLORS["bg_primary"])
        stats_row.pack(fill="x", pady=(0, 20))

        self._stat_card(stats_row, "Today's Revenue", f"${summary['revenue']:.2f}", COLORS["nav_bg"]).pack(side="left", fill="both", expand=True, padx=(0, 10))
        self._stat_card(stats_row, "Transactions", str(summary["total_sales"]), COLORS["accent"]).pack(side="left", fill="both", expand=True, padx=(0, 10))
        self._stat_card(stats_row, "Discounts Given", f"${summary['discounts']:.2f}", COLORS["danger"]).pack(side="left", fill="both", expand=True)

        tk.Label(content, text="Quick Actions", font=FONTS["heading"], bg=COLORS["bg_primary"], fg=COLORS["nav_bg"], anchor="w").pack(fill="x", pady=(0, 10))

        grid = tk.Frame(content, bg=COLORS["bg_primary"])
        grid.pack(fill="x", pady=(0, 20))

        cards = [
            ("\U0001f4b0  POS Terminal", "Open sales terminal", "pos"),
            ("\U0001f4e6  Products", "Manage product catalog", "catalog"),
            ("\U0001f4ca  Inventory", "Stock levels & restocking", "inventory"),
            ("\U0001f4c8  Reports", "Sales analytics & charts", "reports"),
            ("\U0001f3f7\ufe0f  Discounts", "Manage discount codes", "discounts"),
            ("\U0001f465  Users", "Manage staff & roles", "users"),
        ]

        for i, (title, desc, view) in enumerate(cards):
            row, col = divmod(i, 3)
            card = tk.Frame(grid, bg=COLORS["bg_white"], highlightbackground=COLORS["border"], highlightthickness=1, cursor="hand2", padx=20, pady=20)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            grid.columnconfigure(col, weight=1)
            grid.rowconfigure(row, weight=1)

            tk.Label(card, text=title, font=FONTS["heading"], bg=COLORS["bg_white"], fg=COLORS["nav_bg"], anchor="w").pack(anchor="w")
            tk.Label(card, text=desc, font=FONTS["small"], bg=COLORS["bg_white"], fg=COLORS["text_muted"], anchor="w").pack(anchor="w", pady=(4, 0))

            for w in [card] + card.winfo_children():
                w.bind("<Button-1>", lambda e, v=view: self.navigate(v))

    def _stat_card(self, parent, title, value, color):
        frame = tk.Frame(parent, bg=COLORS["bg_white"], padx=18, pady=15, highlightbackground=COLORS["border"], highlightthickness=1)
        tk.Label(frame, text=title, font=FONTS["small"], bg=COLORS["bg_white"], fg=COLORS["text_muted"]).pack(anchor="w")
        tk.Label(frame, text=value, font=FONTS["big_total"], bg=COLORS["bg_white"], fg=color).pack(anchor="w", pady=(5, 0))
        return frame

    def _logout(self):
        self.auth.logout()
        self.navigate("staff_select")


from config import APP_NAME
