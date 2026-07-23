import tkinter as tk
from tkinter import ttk
from utils.theme import COLORS, FONTS, SIZES


class ReportsView(tk.Frame):
    def __init__(self, parent, report_controller, navigate_callback):
        super().__init__(parent, bg=COLORS["bg_primary"])
        self.reports = report_controller
        self.navigate = navigate_callback
        self._build()

    def _build(self):
        nav = tk.Frame(self, bg=COLORS["nav_bg"], height=SIZES["navbar_height"])
        nav.pack(fill="x")
        nav.pack_propagate(False)
        tk.Label(nav, text=f"\u2615  {APP_NAME}", font=FONTS["navbar"], bg=COLORS["nav_bg"], fg=COLORS["text_white"]).pack(side="left", padx=15)
        tk.Label(nav, text="Reports & Analytics", font=FONTS["small"], bg=COLORS["nav_bg"], fg=COLORS["text_white"]).pack(side="left", padx=10)
        tk.Button(nav, text="\u2190 Back", font=FONTS["small"], bg=COLORS["accent"], fg=COLORS["text_dark"], relief="flat", cursor="hand2", padx=12, pady=4, command=lambda: self.navigate("dashboard")).pack(side="right", padx=15)

        period_frame = tk.Frame(self, bg=COLORS["bg_primary"], padx=20, pady=12)
        period_frame.pack(fill="x")

        self.period_var = tk.StringVar(value="today")
        periods = [("today", "Today"), ("yesterday", "Yesterday"), ("week", "This Week"), ("month", "This Month"), ("year", "This Year")]
        for val, text in periods:
            rb = tk.Radiobutton(period_frame, text=text, variable=self.period_var, value=val, font=FONTS["small"], bg=COLORS["bg_primary"], fg=COLORS["text_primary"], selectcolor=COLORS["bg_white"], activebackground=COLORS["bg_primary"], activeforeground=COLORS["nav_bg"], command=self._refresh)
            rb.pack(side="left", padx=(0, 12))

        stats_frame = tk.Frame(self, bg=COLORS["bg_primary"], padx=20)
        stats_frame.pack(fill="x")

        self.revenue_card = self._stat_card(stats_frame, "Revenue", "$0.00", COLORS["nav_bg"])
        self.revenue_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.sales_card = self._stat_card(stats_frame, "Sales", "0", COLORS["accent"])
        self.sales_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.discount_card = self._stat_card(stats_frame, "Discounts", "$0.00", COLORS["danger"])
        self.discount_card.pack(side="left", fill="both", expand=True)

        bottom = tk.Frame(self, bg=COLORS["bg_primary"], padx=20, pady=10)
        bottom.pack(fill="both", expand=True)

        left = tk.Frame(bottom, bg=COLORS["bg_white"], highlightbackground=COLORS["border"], highlightthickness=1, padx=12, pady=12)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(left, text="Sales by Date (Last 7 Days)", font=FONTS["subheading"], bg=COLORS["bg_white"], fg=COLORS["nav_bg"], anchor="w").pack(anchor="w", pady=(0, 8))

        self.chart_canvas = tk.Canvas(left, bg=COLORS["bg_primary"], highlightthickness=0)
        self.chart_canvas.pack(fill="both", expand=True)

        right = tk.Frame(bottom, bg=COLORS["bg_white"], highlightbackground=COLORS["border"], highlightthickness=1, padx=12, pady=12)
        right.pack(side="right", fill="both", expand=True, padx=(10, 0))

        tk.Label(right, text="Top Products", font=FONTS["subheading"], bg=COLORS["bg_white"], fg=COLORS["nav_bg"], anchor="w").pack(anchor="w", pady=(0, 8))

        self.top_tree = ttk.Treeview(right, columns=("product", "qty", "revenue"), show="headings", height=8, style="Treeview")
        self.top_tree.heading("product", text="Product")
        self.top_tree.heading("qty", text="Qty")
        self.top_tree.heading("revenue", text="Revenue")
        self.top_tree.column("product", width=150)
        self.top_tree.column("qty", width=50, anchor="center")
        self.top_tree.column("revenue", width=80, anchor="e")
        self.top_tree.pack(fill="both", expand=True)

        self._refresh()

    def _stat_card(self, parent, title, value, color):
        frame = tk.Frame(parent, bg=COLORS["bg_white"], padx=18, pady=15, highlightbackground=COLORS["border"], highlightthickness=1)
        tk.Label(frame, text=title, font=FONTS["small"], bg=COLORS["bg_white"], fg=COLORS["text_muted"]).pack(anchor="w")
        lbl = tk.Label(frame, text=value, font=FONTS["big_total"], bg=COLORS["bg_white"], fg=color)
        lbl.pack(anchor="w", pady=(5, 0))
        return frame

    def _refresh(self):
        start, end = self.reports.get_date_range(self.period_var.get())
        sales = self.reports.get_sales(start, end)
        total_rev = sum(s["total"] for s in sales)
        total_disc = sum(s["discount_amount"] for s in sales)

        for widget, val in [(self.revenue_card, f"${total_rev:.2f}"), (self.sales_card, str(len(sales))), (self.discount_card, f"${total_disc:.2f}")]:
            for child in widget.winfo_children():
                if isinstance(child, tk.Label) and child.cget("font") == FONTS["big_total"]:
                    child.config(text=val)
                    break

        self.top_tree.delete(*self.top_tree.get_children())
        for p in self.reports.get_top_products(10, start, end):
            self.top_tree.insert("", "end", values=(p["name"], p["total_qty"], f"${p['total_revenue']:.2f}"))

        self._draw_chart()

    def _draw_chart(self):
        self.chart_canvas.delete("all")
        data = self.reports.get_sales_chart_data(7)
        if not data:
            self.chart_canvas.create_text(200, 125, text="No data available", font=FONTS["body"], fill=COLORS["text_muted"])
            return

        max_rev = max(d["revenue"] for d in data) if data else 1
        if max_rev == 0:
            max_rev = 1

        self.chart_canvas.update_idletasks()
        cw = self.chart_canvas.winfo_width() or 400
        ch = self.chart_canvas.winfo_height() or 250
        margin = 45
        bar_w = max(20, (cw - margin * 2) // len(data) - 10) if data else 20
        chart_h = ch - margin * 2

        for i, d in enumerate(data):
            x = margin + i * (bar_w + 10)
            bar_h = (d["revenue"] / max_rev) * chart_h
            y1 = ch - margin
            y2 = y1 - bar_h

            self.chart_canvas.create_rectangle(x, y1, x + bar_w, y2, fill=COLORS["nav_bg"], outline=COLORS["accent"], width=1)
            self.chart_canvas.create_text(x + bar_w // 2, y1 + 15, text=d["sale_date"][-5:], font=FONTS["small"], fill=COLORS["text_muted"])
            self.chart_canvas.create_text(x + bar_w // 2, y2 - 8, text=f"${d['revenue']:.0f}", font=FONTS["small_bold"], fill=COLORS["nav_bg"])


from config import APP_NAME
