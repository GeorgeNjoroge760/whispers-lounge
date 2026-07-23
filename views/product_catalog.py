import tkinter as tk
from tkinter import ttk, messagebox
from utils.theme import COLORS, FONTS, SIZES


class ProductCatalogView(tk.Frame):
    def __init__(self, parent, product_controller, navigate_callback):
        super().__init__(parent, bg=COLORS["bg_primary"])
        self.products = product_controller
        self.navigate = navigate_callback
        self._build()

    def _build(self):
        nav = tk.Frame(self, bg=COLORS["nav_bg"], height=SIZES["navbar_height"])
        nav.pack(fill="x")
        nav.pack_propagate(False)
        tk.Label(nav, text=f"\u2615  {APP_NAME}", font=FONTS["navbar"], bg=COLORS["nav_bg"], fg=COLORS["text_white"]).pack(side="left", padx=15)
        tk.Label(nav, text="Product Catalog", font=FONTS["small"], bg=COLORS["nav_bg"], fg=COLORS["text_white"]).pack(side="left", padx=10)
        tk.Button(nav, text="\u2190 Back", font=FONTS["small"], bg=COLORS["accent"], fg=COLORS["text_dark"], relief="flat", cursor="hand2", padx=12, pady=4, command=lambda: self.navigate("dashboard")).pack(side="right", padx=15)

        toolbar = tk.Frame(self, bg=COLORS["bg_primary"], padx=20, pady=12)
        toolbar.pack(fill="x")
        tk.Button(toolbar, text="+ Add Product", font=FONTS["body_bold"], bg=COLORS["nav_bg"], fg=COLORS["text_white"], relief="flat", cursor="hand2", padx=14, pady=6, command=self._add_product).pack(side="left", padx=(0, 8))
        tk.Button(toolbar, text="+ Add Category", font=FONTS["body_bold"], bg=COLORS["accent"], fg=COLORS["text_dark"], relief="flat", cursor="hand2", padx=14, pady=6, command=self._add_category).pack(side="left")
        tk.Button(toolbar, text="Edit Selected", font=FONTS["body_bold"], bg=COLORS["bg_white"], fg=COLORS["nav_bg"], relief="solid", bd=1, cursor="hand2", padx=14, pady=6, command=self._edit_product).pack(side="left", padx=(8, 0))
        tk.Button(toolbar, text="Delete Selected", font=FONTS["body_bold"], bg=COLORS["danger"], fg=COLORS["text_white"], relief="flat", cursor="hand2", padx=14, pady=6, command=self._delete_product).pack(side="left", padx=(8, 0))

        self.search_var = tk.StringVar()
        tk.Entry(toolbar, textvariable=self.search_var, font=FONTS["body"], bg=COLORS["bg_white"], fg=COLORS["text_primary"], insertbackground=COLORS["text_primary"], relief="solid", bd=1, width=28).pack(side="right", ipady=5)
        self.search_var.trace_add("write", lambda *_: self._refresh())

        tree_frame = tk.Frame(self, bg=COLORS["bg_white"], padx=20, highlightbackground=COLORS["border"], highlightthickness=1)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self.tree = ttk.Treeview(tree_frame, columns=("id", "name", "category", "price", "cost", "stock", "barcode"), show="headings", style="Treeview")
        for col, text, w in [("id", "ID", 50), ("name", "Name", 200), ("category", "Category", 120), ("price", "Price", 80), ("cost", "Cost", 80), ("stock", "Stock", 70), ("barcode", "Barcode", 120)]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w, anchor="center" if col != "name" else "w")

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scroll.pack(side="right", fill="y", pady=10, padx=(0, 10))

        self._refresh()

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        q = self.search_var.get().strip()
        products = self.products.search_products(q) if q else self.products.get_all_products()
        for p in products:
            stock = p["stock_qty"] if p["stock_qty"] is not None else "N/A"
            self.tree.insert("", "end", values=(p["id"], p["name"], p["category_name"] or "-", f"${p['price']:.2f}", f"${p['cost']:.2f}", stock, p["barcode"] or "-"))

    def _get_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a product first")
            return None
        return self.tree.item(sel[0])["values"]

    def _add_product(self):
        self._product_dialog()

    def _edit_product(self):
        vals = self._get_selected()
        if not vals:
            return
        product = self.products.get_product(vals[0])
        if product:
            self._product_dialog(product)

    def _delete_product(self):
        vals = self._get_selected()
        if not vals:
            return
        if messagebox.askyesno("Delete", f"Delete '{vals[1]}'?"):
            self.products.remove_product(vals[0])
            self._refresh()

    def _product_dialog(self, product=None):
        dlg = tk.Toplevel(self)
        dlg.title("Edit Product" if product else "Add Product")
        dlg.geometry("400x400")
        dlg.configure(bg=COLORS["bg_white"])
        dlg.transient(self)
        dlg.grab_set()

        header_bg = tk.Frame(dlg, bg=COLORS["nav_bg"], height=50)
        header_bg.pack(fill="x")
        header_bg.pack_propagate(False)
        tk.Label(header_bg, text="Edit Product" if product else "Add Product", font=FONTS["heading"], bg=COLORS["nav_bg"], fg=COLORS["text_white"]).pack(pady=12)

        form = tk.Frame(dlg, bg=COLORS["bg_white"], padx=25, pady=20)
        form.pack(fill="both", expand=True)

        fields = {}
        for label in ["Name", "Price", "Cost", "Barcode"]:
            tk.Label(form, text=label, font=FONTS["small_bold"], bg=COLORS["bg_white"], fg=COLORS["text_primary"]).pack(anchor="w")
            entry = tk.Entry(form, font=FONTS["body"], bg=COLORS["bg_primary"], fg=COLORS["text_primary"], insertbackground=COLORS["text_primary"], relief="flat", highlightthickness=1, highlightbackground=COLORS["border"])
            entry.pack(pady=(2, 10), ipady=5, fill="x")
            fields[label.lower()] = entry

        tk.Label(form, text="Category", font=FONTS["small_bold"], bg=COLORS["bg_white"], fg=COLORS["text_primary"]).pack(anchor="w")
        cats = self.products.get_categories()
        cat_names = ["None"] + [c["name"] for c in cats]
        cat_map = {c["name"]: c["id"] for c in cats}
        cat_var = tk.StringVar(value="None")
        ttk.Combobox(form, textvariable=cat_var, values=cat_names, state="readonly", width=28).pack(pady=(2, 15), fill="x")

        if product:
            fields["name"].insert(0, product["name"])
            fields["price"].insert(0, f"{product['price']:.2f}")
            fields["cost"].insert(0, f"{product['cost']:.2f}")
            fields["barcode"].insert(0, product["barcode"] or "")
            if product["category_name"] and product["category_name"] in cat_map:
                cat_var.set(product["category_name"])

        def save():
            try:
                name = fields["name"].get().strip()
                price = float(fields["price"].get())
                cost = float(fields["cost"].get())
                barcode = fields["barcode"].get().strip() or None
                cat_name = cat_var.get()
                cat_id = cat_map.get(cat_name) if cat_name != "None" else None
                if product:
                    self.products.edit_product(product["id"], name=name, category_id=cat_id, price=price, cost=cost, barcode=barcode)
                else:
                    self.products.add_product(name, cat_id, price, cost, barcode)
                dlg.destroy()
                self._refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=dlg)

        tk.Button(form, text="Save", font=FONTS["body_bold"], bg=COLORS["nav_bg"], fg=COLORS["text_white"], relief="flat", cursor="hand2", command=save).pack(fill="x", ipady=8)

    def _add_category(self):
        dlg = tk.Toplevel(self)
        dlg.title("Add Category")
        dlg.geometry("300x150")
        dlg.configure(bg=COLORS["bg_white"])
        dlg.transient(self)
        dlg.grab_set()

        form = tk.Frame(dlg, bg=COLORS["bg_white"], padx=20, pady=15)
        form.pack(fill="both", expand=True)

        tk.Label(form, text="Category Name", font=FONTS["small_bold"], bg=COLORS["bg_white"], fg=COLORS["text_primary"]).pack(anchor="w")
        entry = tk.Entry(form, font=FONTS["body"], bg=COLORS["bg_primary"], fg=COLORS["text_primary"], insertbackground=COLORS["text_primary"], relief="flat", highlightthickness=1, highlightbackground=COLORS["border"])
        entry.pack(pady=(2, 10), ipady=5, fill="x")
        entry.focus_set()

        def save():
            name = entry.get().strip()
            if not name:
                messagebox.showwarning("Error", "Enter a name", parent=dlg)
                return
            try:
                self.products.add_category(name)
                dlg.destroy()
                self._refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=dlg)

        entry.bind("<Return>", lambda e: save())
        tk.Button(form, text="Add", font=FONTS["body_bold"], bg=COLORS["nav_bg"], fg=COLORS["text_white"], relief="flat", cursor="hand2", command=save).pack(fill="x", ipady=6)


from config import APP_NAME
