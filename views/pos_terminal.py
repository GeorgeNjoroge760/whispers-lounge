import tkinter as tk
from tkinter import ttk, messagebox
from utils.theme import COLORS, FONTS, SIZES


class POSTerminalView(tk.Frame):
    def __init__(self, parent, sales_controller, product_controller, auth_controller, navigate_callback):
        super().__init__(parent, bg=COLORS["bg_primary"])
        self.sales = sales_controller
        self.products = product_controller
        self.auth = auth_controller
        self.navigate = navigate_callback
        self.selected_category = None
        self._build()

    def _build(self):
        nav = tk.Frame(self, bg=COLORS["nav_bg"], height=SIZES["navbar_height"])
        nav.pack(fill="x")
        nav.pack_propagate(False)

        user = self.auth.get_current_user()
        tk.Label(nav, text=f"\u2615  {APP_NAME}", font=FONTS["navbar"], bg=COLORS["nav_bg"], fg=COLORS["text_white"]).pack(side="left", padx=15)

        right_nav = tk.Frame(nav, bg=COLORS["nav_bg"])
        right_nav.pack(side="right", padx=15)

        tk.Label(right_nav, text=f"\U0001f464 {user['full_name']}", font=FONTS["small"], bg=COLORS["nav_bg"], fg=COLORS["text_white"]).pack(side="left", padx=(0, 15))

        tk.Button(right_nav, text="Reports", font=FONTS["small"], bg=COLORS["accent"], fg=COLORS["text_dark"], relief="flat", cursor="hand2", padx=12, pady=4, command=lambda: self.navigate("reports")).pack(side="left", padx=(0, 5))
        tk.Button(right_nav, text="Products", font=FONTS["small"], bg=COLORS["accent"], fg=COLORS["text_dark"], relief="flat", cursor="hand2", padx=12, pady=4, command=lambda: self.navigate("catalog")).pack(side="left", padx=(0, 5))
        tk.Button(right_nav, text="Inventory", font=FONTS["small"], bg=COLORS["accent"], fg=COLORS["text_dark"], relief="flat", cursor="hand2", padx=12, pady=4, command=lambda: self.navigate("inventory")).pack(side="left", padx=(0, 5))

        if self.auth.can_manage_users():
            tk.Button(right_nav, text="Users", font=FONTS["small"], bg=COLORS["accent"], fg=COLORS["text_dark"], relief="flat", cursor="hand2", padx=12, pady=4, command=lambda: self.navigate("users")).pack(side="left", padx=(0, 5))
            tk.Button(right_nav, text="Discounts", font=FONTS["small"], bg=COLORS["accent"], fg=COLORS["text_dark"], relief="flat", cursor="hand2", padx=12, pady=4, command=lambda: self.navigate("discounts")).pack(side="left", padx=(0, 5))

        tk.Button(right_nav, text="\u2190 Logout", font=FONTS["small"], bg=COLORS["danger"], fg=COLORS["text_white"], relief="flat", cursor="hand2", padx=12, pady=4, command=self._logout).pack(side="left")

        main = tk.Frame(self, bg=COLORS["bg_primary"])
        main.pack(fill="both", expand=True)

        left = tk.Frame(main, bg=COLORS["bg_primary"])
        left.pack(side="left", fill="both", expand=True)

        cat_frame = tk.Frame(left, bg=COLORS["bg_primary"], height=SIZES["cat_bar_height"])
        cat_frame.pack(fill="x", padx=10, pady=(10, 0))
        cat_frame.pack_propagate(False)

        self.cat_buttons = []
        btn = tk.Button(cat_frame, text="All", font=FONTS["cat_btn"], bg=COLORS["accent"], fg=COLORS["text_dark"], relief="flat", cursor="hand2", padx=14, pady=4, command=lambda: self._select_category(None))
        btn.pack(side="left", padx=(0, 5))
        self.cat_buttons.append((None, btn))

        for cat in self.products.get_categories():
            btn = tk.Button(cat_frame, text=cat["name"], font=FONTS["cat_btn"], bg=COLORS["bg_white"], fg=COLORS["text_primary"], relief="solid", bd=1, cursor="hand2", padx=14, pady=4, command=lambda c=cat: self._select_category(c["id"]))
            btn.pack(side="left", padx=(0, 5))
            self.cat_buttons.append((cat["id"], btn))

        search_frame = tk.Frame(left, bg=COLORS["bg_primary"])
        search_frame.pack(fill="x", padx=10, pady=8)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=FONTS["body"], bg=COLORS["bg_white"], fg=COLORS["text_primary"], insertbackground=COLORS["text_primary"], relief="solid", bd=1, highlightthickness=1, highlightbackground=COLORS["border"])
        search_entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))
        search_entry.bind("<KeyRelease>", lambda e: self._filter_products())
        tk.Button(search_frame, text="\u2716", font=FONTS["small"], bg=COLORS["bg_white"], fg=COLORS["text_muted"], relief="flat", cursor="hand2", command=lambda: (self.search_var.set(""), self._filter_products())).pack(side="right", ipady=2)

        self.product_canvas = tk.Canvas(left, bg=COLORS["bg_primary"], highlightthickness=0)
        self.product_scrollbar = ttk.Scrollbar(left, orient="vertical", command=self.product_canvas.yview)
        self.product_grid_frame = tk.Frame(self.product_canvas, bg=COLORS["bg_primary"])

        self.product_grid_frame.bind("<Configure>", lambda e: self.product_canvas.configure(scrollregion=self.product_canvas.bbox("all")))
        self.product_canvas.create_window((0, 0), window=self.product_grid_frame, anchor="nw")
        self.product_canvas.configure(yscrollcommand=self.product_scrollbar.set)

        self.product_canvas.pack(side="left", fill="both", expand=True)
        self.product_scrollbar.pack(side="right", fill="y")

        right = tk.Frame(main, bg=COLORS["bg_white"], width=SIZES["cart_width"], highlightbackground=COLORS["border"], highlightthickness=1)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        cart_header = tk.Frame(right, bg=COLORS["nav_bg"], height=44)
        cart_header.pack(fill="x")
        cart_header.pack_propagate(False)
        tk.Label(cart_header, text="\U0001f6d2  Current Order", font=FONTS["subheading"], bg=COLORS["nav_bg"], fg=COLORS["text_white"]).pack(side="left", padx=12, pady=8)

        self.cart_frame = tk.Frame(right, bg=COLORS["bg_white"])
        self.cart_frame.pack(fill="both", expand=True)

        self.cart_canvas = tk.Canvas(self.cart_frame, bg=COLORS["bg_white"], highlightthickness=0)
        self.cart_scrollbar = ttk.Scrollbar(self.cart_frame, orient="vertical", command=self.cart_canvas.yview)
        self.cart_inner = tk.Frame(self.cart_canvas, bg=COLORS["bg_white"])

        self.cart_inner.bind("<Configure>", lambda e: self.cart_canvas.configure(scrollregion=self.cart_canvas.bbox("all")))
        self.cart_canvas.create_window((0, 0), window=self.cart_inner, anchor="nw")
        self.cart_canvas.configure(yscrollcommand=self.cart_scrollbar.set)
        self.cart_canvas.pack(side="left", fill="both", expand=True)
        self.cart_scrollbar.pack(side="right", fill="y")

        bottom = tk.Frame(right, bg=COLORS["bg_white"], highlightbackground=COLORS["border"], highlightthickness=1)
        bottom.pack(fill="x", side="bottom")

        disc_row = tk.Frame(bottom, bg=COLORS["bg_white"], padx=12, pady=6)
        disc_row.pack(fill="x")
        self.disc_var = tk.StringVar()
        tk.Entry(disc_row, textvariable=self.disc_var, font=FONTS["small"], bg=COLORS["bg_primary"], fg=COLORS["text_primary"], insertbackground=COLORS["text_primary"], relief="flat", width=16).pack(side="left", ipady=3, padx=(0, 4))
        tk.Button(disc_row, text="Apply", font=FONTS["small"], bg=COLORS["accent"], fg=COLORS["text_dark"], relief="flat", cursor="hand2", padx=8, command=self._apply_discount).pack(side="left")
        self.disc_label = tk.Label(disc_row, text="", font=FONTS["tiny"], bg=COLORS["bg_white"], fg=COLORS["nav_bg"])
        self.disc_label.pack(side="right")

        totals = tk.Frame(bottom, bg=COLORS["bg_white"], padx=12, pady=4)
        totals.pack(fill="x")
        self.subtotal_label = tk.Label(totals, text="Subtotal: $0.00", font=FONTS["body"], bg=COLORS["bg_white"], fg=COLORS["text_muted"], anchor="w")
        self.subtotal_label.pack(fill="x")
        self.total_label = tk.Label(totals, text="TOTAL: $0.00", font=FONTS["big_total"], bg=COLORS["bg_white"], fg=COLORS["nav_bg"], anchor="w")
        self.total_label.pack(fill="x")

        pay_row = tk.Frame(bottom, bg=COLORS["bg_white"], padx=12, pady=2)
        pay_row.pack(fill="x")
        self.pay_var = tk.StringVar(value="Cash")
        for method in ["Cash", "Card", "Mobile"]:
            tk.Radiobutton(pay_row, text=method, variable=self.pay_var, value=method, font=FONTS["small"], bg=COLORS["bg_white"], fg=COLORS["text_primary"], selectcolor=COLORS["bg_primary"], activebackground=COLORS["bg_white"], activeforeground=COLORS["nav_bg"]).pack(side="left", padx=(0, 10))

        btn_row = tk.Frame(bottom, bg=COLORS["bg_white"], padx=12, pady=10)
        btn_row.pack(fill="x")
        tk.Button(btn_row, text="Clear Cart", font=FONTS["body"], bg=COLORS["bg_white"], fg=COLORS["danger"], relief="solid", bd=1, cursor="hand2", padx=10, pady=6, command=self._clear_cart).pack(side="left")
        tk.Button(btn_row, text="COMPLETE SALE", font=FONTS["heading"], bg=COLORS["nav_bg"], fg=COLORS["text_white"], relief="flat", cursor="hand2", command=self._complete_sale).pack(side="right", ipady=4)

        self._load_products()

    def _select_category(self, cat_id):
        self.selected_category = cat_id
        for cid, btn in self.cat_buttons:
            if cid == cat_id:
                btn.config(bg=COLORS["accent"], fg=COLORS["text_dark"])
            else:
                btn.config(bg=COLORS["bg_white"], fg=COLORS["text_primary"])
        self._filter_products()

    def _filter_products(self):
        query = self.search_var.get().strip()
        if query:
            products = self.products.search_products(query)
        else:
            products = self.products.get_all_products(category_id=self.selected_category)
        self._display_products(products)

    def _load_products(self):
        products = self.products.get_all_products(category_id=self.selected_category)
        self._display_products(products)

    def _display_products(self, products):
        for w in self.product_grid_frame.winfo_children():
            w.destroy()

        self.product_canvas.update_idletasks()
        canvas_w = self.product_canvas.winfo_width() or 600
        cols = max(1, canvas_w // SIZES["product_min_w"])

        for i, p in enumerate(products):
            row, col = divmod(i, cols)

            card = tk.Frame(self.product_grid_frame, bg=COLORS["bg_white"], highlightbackground=COLORS["border"], highlightthickness=1, cursor="hand2")
            card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
            self.product_grid_frame.columnconfigure(col, weight=1)

            inner = tk.Frame(card, bg=COLORS["bg_white"], padx=8, pady=8)
            inner.pack(fill="both", expand=True)

            stock = p["stock_qty"] if p["stock_qty"] is not None else 0
            if stock <= 0:
                dot_color = COLORS["stock_zero"]
            elif stock <= 5:
                dot_color = COLORS["stock_low"]
            else:
                dot_color = COLORS["stock_ok"]

            top_row = tk.Frame(inner, bg=COLORS["bg_white"])
            top_row.pack(fill="x")
            tk.Label(top_row, text=p["name"], font=FONTS["product_name"], bg=COLORS["bg_white"], fg=COLORS["text_primary"], anchor="w", wraplength=120).pack(side="left", fill="x", expand=True)
            tk.Canvas(top_row, width=10, height=10, bg=COLORS["bg_white"], highlightthickness=0).pack(side="right", padx=(4, 0))
            dot = tk.Canvas(inner, width=10, height=10, bg=COLORS["bg_white"], highlightthickness=0)
            dot.pack(anchor="e")
            dot.create_ellipse(1, 1, 9, 9, fill=dot_color, outline="white", width=2)

            tk.Label(inner, text=f"${p['price']:.2f}", font=FONTS["product_price"], bg=COLORS["bg_white"], fg=COLORS["accent"], anchor="w").pack(anchor="w", pady=(2, 0))
            tk.Label(inner, text=f"Stock: {stock}", font=FONTS["product_stock"], bg=COLORS["bg_white"], fg=COLORS["text_muted"], anchor="w").pack(anchor="w")

            for widget in [card, inner] + inner.winfo_children():
                widget.bind("<Button-1>", lambda e, prod=p: self._add_to_cart(prod))

    def _add_to_cart(self, product):
        if product["stock_qty"] is not None and product["stock_qty"] <= 0:
            messagebox.showwarning("Out of Stock", f"{product['name']} is out of stock!")
            return
        self.sales.add_to_cart(product)
        self._refresh_cart()

    def _refresh_cart(self):
        for w in self.cart_inner.winfo_children():
            w.destroy()

        cart = self.sales.get_cart()
        if not cart:
            tk.Label(self.cart_inner, text="Cart is empty", font=FONTS["small"], bg=COLORS["bg_white"], fg=COLORS["text_muted"]).pack(pady=40)
        else:
            for i, item in enumerate(cart):
                row = tk.Frame(self.cart_inner, bg=COLORS["bg_white"], padx=10, pady=6)
                row.pack(fill="x")
                tk.Frame(row, bg=COLORS["accent"], width=3).pack(side="left", fill="y", padx=(0, 8))

                info = tk.Frame(row, bg=COLORS["bg_white"])
                info.pack(side="left", fill="x", expand=True)

                name_row = tk.Frame(info, bg=COLORS["bg_white"])
                name_row.pack(fill="x")
                tk.Label(name_row, text=item["name"], font=FONTS["cart_item"], bg=COLORS["bg_white"], fg=COLORS["text_primary"], anchor="w").pack(side="left")
                tk.Label(name_row, text=f"${item['subtotal']:.2f}", font=FONTS["cart_price"], bg=COLORS["bg_white"], fg=COLORS["nav_bg"], anchor="e").pack(side="right")

                ctrl_row = tk.Frame(info, bg=COLORS["bg_white"])
                ctrl_row.pack(fill="x", pady=(2, 0))
                tk.Button(ctrl_row, text="-", font=FONTS["small"], bg=COLORS["bg_primary"], fg=COLORS["text_primary"], relief="flat", width=3, cursor="hand2", command=lambda idx=i: self._change_qty(idx, -1)).pack(side="left")
                tk.Label(ctrl_row, text=str(item["qty"]), font=FONTS["body_bold"], bg=COLORS["bg_white"], fg=COLORS["text_primary"], width=4).pack(side="left")
                tk.Button(ctrl_row, text="+", font=FONTS["small"], bg=COLORS["bg_primary"], fg=COLORS["text_primary"], relief="flat", width=3, cursor="hand2", command=lambda idx=i: self._change_qty(idx, 1)).pack(side="left")
                tk.Button(ctrl_row, text="\u2716", font=FONTS["tiny"], bg=COLORS["bg_white"], fg=COLORS["danger"], relief="flat", cursor="hand2", command=lambda idx=i: self._remove_item(idx)).pack(side="right")

        self.subtotal_label.config(text=f"Subtotal: ${self.sales.get_cart_subtotal():.2f}")
        self.total_label.config(text=f"TOTAL: ${self.sales.get_cart_total():.2f}")

    def _change_qty(self, idx, delta):
        cart = self.sales.get_cart()
        new_qty = cart[idx]["qty"] + delta
        self.sales.update_cart_qty(idx, new_qty)
        self._refresh_cart()

    def _remove_item(self, idx):
        self.sales.remove_from_cart(idx)
        self._refresh_cart()

    def _clear_cart(self):
        self.sales.clear_cart()
        self.disc_label.config(text="")
        self.disc_var.set("")
        self._refresh_cart()

    def _apply_discount(self):
        code = self.disc_var.get().strip()
        if not code:
            return
        ok, msg = self.sales.apply_discount(code)
        if ok:
            self.disc_label.config(text=msg, fg=COLORS["nav_bg"])
        else:
            self.disc_label.config(text=msg, fg=COLORS["danger"])
        self._refresh_cart()

    def _complete_sale(self):
        cart = self.sales.get_cart()
        if not cart:
            messagebox.showwarning("Empty Cart", "Add items to the cart first!")
            return
        total = self.sales.get_cart_total()
        result = messagebox.askyesno("Complete Sale", f"Total: ${total:.2f}\nPayment: {self.pay_var.get()}\n\nComplete this sale?")
        if not result:
            return
        try:
            user = self.auth.get_current_user()
            sale_id, receipt_path, receipt_text = self.sales.finalize_sale(user["id"], self.pay_var.get())
            self.disc_label.config(text="")
            self.disc_var.set("")
            self._refresh_cart()
            self._load_products()
            self._show_receipt(sale_id, receipt_text)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _show_receipt(self, sale_id, receipt_text):
        dlg = tk.Toplevel(self)
        dlg.title(f"Receipt #{sale_id}")
        dlg.geometry("380x480")
        dlg.configure(bg=COLORS["bg_white"])
        dlg.transient(self)

        tk.Label(dlg, text="\u2705  Sale Complete!", font=FONTS["heading"], bg=COLORS["bg_white"], fg=COLORS["nav_bg"]).pack(pady=12)
        tk.Label(dlg, text=f"Receipt #{sale_id}", font=FONTS["small"], bg=COLORS["bg_white"], fg=COLORS["text_muted"]).pack()

        txt = tk.Text(dlg, font=FONTS["mono"], bg=COLORS["bg_primary"], fg=COLORS["text_primary"], wrap="word", relief="solid", bd=1, padx=10, pady=10)
        txt.pack(fill="both", expand=True, padx=15, pady=10)
        txt.insert("1.0", receipt_text)
        txt.config(state="disabled")

        tk.Button(dlg, text="Close", font=FONTS["body_bold"], bg=COLORS["nav_bg"], fg=COLORS["text_white"], relief="flat", cursor="hand2", command=dlg.destroy).pack(pady=(0, 12), ipadx=20, ipady=6)

    def _logout(self):
        self.sales.clear_cart()
        self.auth.logout()
        self.navigate("staff_select")


from config import APP_NAME
