import tkinter as tk
from tkinter import ttk, messagebox
from utils.theme import COLORS, FONTS, SIZES


class DiscountsView(tk.Frame):
    def __init__(self, parent, db, navigate_callback):
        super().__init__(parent, bg=COLORS["bg_primary"])
        from models.discount import DiscountModel
        self.model = DiscountModel(db)
        self.navigate = navigate_callback
        self._build()

    def _build(self):
        nav = tk.Frame(self, bg=COLORS["nav_bg"], height=SIZES["navbar_height"])
        nav.pack(fill="x")
        nav.pack_propagate(False)
        tk.Label(nav, text=f"\u2615  {APP_NAME}", font=FONTS["navbar"], bg=COLORS["nav_bg"], fg=COLORS["text_white"]).pack(side="left", padx=15)
        tk.Label(nav, text="Discounts", font=FONTS["small"], bg=COLORS["nav_bg"], fg=COLORS["text_white"]).pack(side="left", padx=10)
        tk.Button(nav, text="\u2190 Back", font=FONTS["small"], bg=COLORS["accent"], fg=COLORS["text_dark"], relief="flat", cursor="hand2", padx=12, pady=4, command=lambda: self.navigate("dashboard")).pack(side="right", padx=15)

        toolbar = tk.Frame(self, bg=COLORS["bg_primary"], padx=20, pady=12)
        toolbar.pack(fill="x")
        tk.Button(toolbar, text="+ Add Discount", font=FONTS["body_bold"], bg=COLORS["nav_bg"], fg=COLORS["text_white"], relief="flat", cursor="hand2", padx=14, pady=6, command=self._add_discount).pack(side="left", padx=(0, 8))
        tk.Button(toolbar, text="Delete Selected", font=FONTS["body_bold"], bg=COLORS["danger"], fg=COLORS["text_white"], relief="flat", cursor="hand2", padx=14, pady=6, command=self._delete_discount).pack(side="left")

        tree_frame = tk.Frame(self, bg=COLORS["bg_white"], padx=20, highlightbackground=COLORS["border"], highlightthickness=1)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self.tree = ttk.Treeview(tree_frame, columns=("id", "code", "type", "value", "min_purchase", "valid_until"), show="headings", style="Treeview")
        for col, text, w in [("id", "ID", 50), ("code", "Code", 120), ("type", "Type", 100), ("value", "Value", 100), ("min_purchase", "Min Purchase", 120), ("valid_until", "Valid Until", 150)]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w, anchor="center")

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scroll.pack(side="right", fill="y", pady=10, padx=(0, 10))

        self._refresh()

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        for d in self.model.get_all():
            dtype = "Percentage" if d["discount_type"] == "percentage" else "Fixed"
            val = f"{d['value']}%" if d["discount_type"] == "percentage" else f"${d['value']:.2f}"
            self.tree.insert("", "end", values=(d["id"], d["code"], dtype, val, f"${d['min_purchase']:.2f}", d["valid_until"] or "No expiry"))

    def _add_discount(self):
        dlg = tk.Toplevel(self)
        dlg.title("Add Discount")
        dlg.geometry("380x380")
        dlg.configure(bg=COLORS["bg_white"])
        dlg.transient(self)
        dlg.grab_set()

        header = tk.Frame(dlg, bg=COLORS["nav_bg"], height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="Add Discount", font=FONTS["heading"], bg=COLORS["nav_bg"], fg=COLORS["text_white"]).pack(pady=12)

        form = tk.Frame(dlg, bg=COLORS["bg_white"], padx=25, pady=20)
        form.pack(fill="both", expand=True)

        fields = {}
        for label in ["Code", "Value"]:
            tk.Label(form, text=label, font=FONTS["small_bold"], bg=COLORS["bg_white"], fg=COLORS["text_primary"]).pack(anchor="w")
            entry = tk.Entry(form, font=FONTS["body"], bg=COLORS["bg_primary"], fg=COLORS["text_primary"], insertbackground=COLORS["text_primary"], relief="flat", highlightthickness=1, highlightbackground=COLORS["border"])
            entry.pack(pady=(2, 10), ipady=5, fill="x")
            fields[label.lower()] = entry

        tk.Label(form, text="Type", font=FONTS["small_bold"], bg=COLORS["bg_white"], fg=COLORS["text_primary"]).pack(anchor="w")
        type_var = tk.StringVar(value="percentage")
        type_frame = tk.Frame(form, bg=COLORS["bg_white"])
        type_frame.pack(fill="x", pady=(2, 10))
        tk.Radiobutton(type_frame, text="Percentage", variable=type_var, value="percentage", font=FONTS["small"], bg=COLORS["bg_white"], fg=COLORS["text_primary"], selectcolor=COLORS["bg_primary"]).pack(side="left")
        tk.Radiobutton(type_frame, text="Fixed ($)", variable=type_var, value="fixed", font=FONTS["small"], bg=COLORS["bg_white"], fg=COLORS["text_primary"], selectcolor=COLORS["bg_primary"]).pack(side="left", padx=(15, 0))

        tk.Label(form, text="Min Purchase ($)", font=FONTS["small_bold"], bg=COLORS["bg_white"], fg=COLORS["text_primary"]).pack(anchor="w")
        min_var = tk.StringVar(value="0")
        tk.Entry(form, textvariable=min_var, font=FONTS["body"], bg=COLORS["bg_primary"], fg=COLORS["text_primary"], insertbackground=COLORS["text_primary"], relief="flat", highlightthickness=1, highlightbackground=COLORS["border"]).pack(pady=(2, 10), ipady=5, fill="x")

        tk.Label(form, text="Valid Until (YYYY-MM-DD, optional)", font=FONTS["small_bold"], bg=COLORS["bg_white"], fg=COLORS["text_primary"]).pack(anchor="w")
        until_var = tk.StringVar()
        tk.Entry(form, textvariable=until_var, font=FONTS["body"], bg=COLORS["bg_primary"], fg=COLORS["text_primary"], insertbackground=COLORS["text_primary"], relief="flat", highlightthickness=1, highlightbackground=COLORS["border"]).pack(pady=(2, 10), ipady=5, fill="x")

        def save():
            try:
                code = fields["code"].get().strip().upper()
                value = float(fields["value"].get())
                min_p = float(min_var.get())
                until = until_var.get().strip() or None
                self.model.create(code, type_var.get(), value, min_p, until)
                dlg.destroy()
                self._refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=dlg)

        tk.Button(form, text="Create", font=FONTS["body_bold"], bg=COLORS["nav_bg"], fg=COLORS["text_white"], relief="flat", cursor="hand2", command=save).pack(fill="x", ipady=8)

    def _delete_discount(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a discount first")
            return
        vals = self.tree.item(sel[0])["values"]
        if messagebox.askyesno("Delete", f"Delete discount '{vals[1]}'?"):
            self.model.delete(vals[0])
            self._refresh()


from config import APP_NAME
