import tkinter as tk
from tkinter import ttk, messagebox
from utils.theme import COLORS, FONTS, SIZES


class InventoryView(tk.Frame):
    def __init__(self, parent, inventory_controller, navigate_callback):
        super().__init__(parent, bg=COLORS["bg_primary"])
        self.inventory = inventory_controller
        self.navigate = navigate_callback
        self._build()

    def _build(self):
        nav = tk.Frame(self, bg=COLORS["nav_bg"], height=SIZES["navbar_height"])
        nav.pack(fill="x")
        nav.pack_propagate(False)
        tk.Label(nav, text=f"\u2615  {APP_NAME}", font=FONTS["navbar"], bg=COLORS["nav_bg"], fg=COLORS["text_white"]).pack(side="left", padx=15)
        tk.Label(nav, text="Inventory", font=FONTS["small"], bg=COLORS["nav_bg"], fg=COLORS["text_white"]).pack(side="left", padx=10)
        tk.Button(nav, text="\u2190 Back", font=FONTS["small"], bg=COLORS["accent"], fg=COLORS["text_dark"], relief="flat", cursor="hand2", padx=12, pady=4, command=lambda: self.navigate("dashboard")).pack(side="right", padx=15)

        toolbar = tk.Frame(self, bg=COLORS["bg_primary"], padx=20, pady=12)
        toolbar.pack(fill="x")
        tk.Button(toolbar, text="Restock Selected", font=FONTS["body_bold"], bg=COLORS["nav_bg"], fg=COLORS["text_white"], relief="flat", cursor="hand2", padx=14, pady=6, command=self._restock).pack(side="left", padx=(0, 8))
        tk.Button(toolbar, text="Set Min Level", font=FONTS["body_bold"], bg=COLORS["accent"], fg=COLORS["text_dark"], relief="flat", cursor="hand2", padx=14, pady=6, command=self._set_min_level).pack(side="left", padx=(0, 8))
        tk.Button(toolbar, text="Show Low Stock", font=FONTS["body_bold"], bg=COLORS["danger"], fg=COLORS["text_white"], relief="flat", cursor="hand2", padx=14, pady=6, command=self._show_low_stock).pack(side="left")
        tk.Button(toolbar, text="Show All", font=FONTS["body_bold"], bg=COLORS["bg_white"], fg=COLORS["text_primary"], relief="solid", bd=1, cursor="hand2", padx=14, pady=6, command=lambda: self._refresh()).pack(side="left", padx=(8, 0))

        tree_frame = tk.Frame(self, bg=COLORS["bg_white"], padx=20, highlightbackground=COLORS["border"], highlightthickness=1)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self.tree = ttk.Treeview(tree_frame, columns=("id", "product", "stock", "min_level", "last_restock"), show="headings", style="Treeview")
        for col, text, w in [("id", "ID", 50), ("product", "Product", 250), ("stock", "Stock", 100), ("min_level", "Min Level", 100), ("last_restock", "Last Restocked", 180)]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w, anchor="center" if col != "product" else "w")

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scroll.pack(side="right", fill="y", pady=10, padx=(0, 10))

        self._refresh()

    def _refresh(self, low_only=False):
        self.tree.delete(*self.tree.get_children())
        items = self.inventory.get_low_stock() if low_only else self.inventory.get_all_stock()
        for item in items:
            if not item["is_active"]:
                continue
            tag = "low" if item["stock_qty"] <= item["min_stock_level"] else "ok"
            self.tree.insert("", "end", values=(
                item["product_id"], item["product_name"], item["stock_qty"],
                item["min_stock_level"], item["last_restocked"] or "Never"
            ), tags=(tag,))
        self.tree.tag_configure("low", foreground=COLORS["danger"])
        self.tree.tag_configure("ok", foreground=COLORS["nav_bg"])

    def _get_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select an item first")
            return None
        return self.tree.item(sel[0])["values"]

    def _show_low_stock(self):
        self._refresh(low_only=True)

    def _restock(self):
        vals = self._get_selected()
        if not vals:
            return
        dlg = tk.Toplevel(self)
        dlg.title("Restock")
        dlg.geometry("350x200")
        dlg.configure(bg=COLORS["bg_white"])
        dlg.transient(self)
        dlg.grab_set()

        header = tk.Frame(dlg, bg=COLORS["nav_bg"], height=44)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="Restock Product", font=FONTS["subheading"], bg=COLORS["nav_bg"], fg=COLORS["text_white"]).pack(pady=10)

        form = tk.Frame(dlg, bg=COLORS["bg_white"], padx=20, pady=15)
        form.pack(fill="both", expand=True)

        tk.Label(form, text=f"{vals[1]}  |  Current: {vals[2]}", font=FONTS["body"], bg=COLORS["bg_white"], fg=COLORS["text_primary"]).pack(anchor="w", pady=(0, 8))
        tk.Label(form, text="Add quantity:", font=FONTS["small_bold"], bg=COLORS["bg_white"], fg=COLORS["text_primary"]).pack(anchor="w")
        qty_var = tk.StringVar(value="10")
        tk.Entry(form, textvariable=qty_var, font=FONTS["body"], bg=COLORS["bg_primary"], fg=COLORS["text_primary"], insertbackground=COLORS["text_primary"], relief="flat", highlightthickness=1, highlightbackground=COLORS["border"]).pack(fill="x", ipady=5, pady=(2, 8))

        def do_restock():
            try:
                qty = int(qty_var.get())
                self.inventory.restock_product(vals[0], qty)
                dlg.destroy()
                self._refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=dlg)

        tk.Button(form, text="Restock", font=FONTS["body_bold"], bg=COLORS["nav_bg"], fg=COLORS["text_white"], relief="flat", cursor="hand2", command=do_restock).pack(fill="x", ipady=6)

    def _set_min_level(self):
        vals = self._get_selected()
        if not vals:
            return
        dlg = tk.Toplevel(self)
        dlg.title("Set Minimum Level")
        dlg.geometry("350x180")
        dlg.configure(bg=COLORS["bg_white"])
        dlg.transient(self)
        dlg.grab_set()

        header = tk.Frame(dlg, bg=COLORS["nav_bg"], height=44)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="Set Minimum Level", font=FONTS["subheading"], bg=COLORS["nav_bg"], fg=COLORS["text_white"]).pack(pady=10)

        form = tk.Frame(dlg, bg=COLORS["bg_white"], padx=20, pady=15)
        form.pack(fill="both", expand=True)

        tk.Label(form, text=f"Min Level for: {vals[1]}", font=FONTS["body"], bg=COLORS["bg_white"], fg=COLORS["text_primary"]).pack(anchor="w", pady=(0, 8))
        level_var = tk.StringVar(value=str(vals[3]))
        tk.Entry(form, textvariable=level_var, font=FONTS["body"], bg=COLORS["bg_primary"], fg=COLORS["text_primary"], insertbackground=COLORS["text_primary"], relief="flat", highlightthickness=1, highlightbackground=COLORS["border"]).pack(fill="x", ipady=5)

        def save():
            try:
                self.inventory.set_min_level(vals[0], int(level_var.get()))
                dlg.destroy()
                self._refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=dlg)

        tk.Button(form, text="Save", font=FONTS["body_bold"], bg=COLORS["nav_bg"], fg=COLORS["text_white"], relief="flat", cursor="hand2", command=save).pack(fill="x", pady=(8, 0), ipady=6)


from config import APP_NAME
