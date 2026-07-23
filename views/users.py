import tkinter as tk
from tkinter import ttk, messagebox
from utils.theme import COLORS, FONTS, SIZES


class UsersView(tk.Frame):
    def __init__(self, parent, db, navigate_callback):
        super().__init__(parent, bg=COLORS["bg_primary"])
        from models.user import UserModel
        self.model = UserModel(db)
        self.navigate = navigate_callback
        self._build()

    def _build(self):
        nav = tk.Frame(self, bg=COLORS["nav_bg"], height=SIZES["navbar_height"])
        nav.pack(fill="x")
        nav.pack_propagate(False)
        tk.Label(nav, text=f"\u2615  {APP_NAME}", font=FONTS["navbar"], bg=COLORS["nav_bg"], fg=COLORS["text_white"]).pack(side="left", padx=15)
        tk.Label(nav, text="User Management", font=FONTS["small"], bg=COLORS["nav_bg"], fg=COLORS["text_white"]).pack(side="left", padx=10)
        tk.Button(nav, text="\u2190 Back", font=FONTS["small"], bg=COLORS["accent"], fg=COLORS["text_dark"], relief="flat", cursor="hand2", padx=12, pady=4, command=lambda: self.navigate("dashboard")).pack(side="right", padx=15)

        toolbar = tk.Frame(self, bg=COLORS["bg_primary"], padx=20, pady=12)
        toolbar.pack(fill="x")
        tk.Button(toolbar, text="+ Add User", font=FONTS["body_bold"], bg=COLORS["nav_bg"], fg=COLORS["text_white"], relief="flat", cursor="hand2", padx=14, pady=6, command=self._add_user).pack(side="left", padx=(0, 8))
        tk.Button(toolbar, text="Edit Selected", font=FONTS["body_bold"], bg=COLORS["accent"], fg=COLORS["text_dark"], relief="flat", cursor="hand2", padx=14, pady=6, command=self._edit_user).pack(side="left", padx=(0, 8))
        tk.Button(toolbar, text="Deactivate", font=FONTS["body_bold"], bg=COLORS["danger"], fg=COLORS["text_white"], relief="flat", cursor="hand2", padx=14, pady=6, command=self._deactivate_user).pack(side="left", padx=(0, 8))
        tk.Button(toolbar, text="Change Password", font=FONTS["body_bold"], bg=COLORS["bg_white"], fg=COLORS["nav_bg"], relief="solid", bd=1, cursor="hand2", padx=14, pady=6, command=self._change_password).pack(side="left")

        tree_frame = tk.Frame(self, bg=COLORS["bg_white"], padx=20, highlightbackground=COLORS["border"], highlightthickness=1)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self.tree = ttk.Treeview(tree_frame, columns=("id", "username", "full_name", "role", "active", "created"), show="headings", style="Treeview")
        for col, text, w in [("id", "ID", 50), ("username", "Username", 120), ("full_name", "Full Name", 200), ("role", "Role", 100), ("active", "Active", 80), ("created", "Created", 150)]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w, anchor="center" if col not in ("full_name",) else "w")

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scroll.pack(side="right", fill="y", pady=10, padx=(0, 10))

        self._refresh()

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        for u in self.model.get_all():
            active = "Yes" if u["is_active"] else "No"
            tag = "active" if u["is_active"] else "inactive"
            self.tree.insert("", "end", values=(u["id"], u["username"], u["full_name"], u["role"].capitalize(), active, u["created_at"]), tags=(tag,))
        self.tree.tag_configure("active", foreground=COLORS["nav_bg"])
        self.tree.tag_configure("inactive", foreground=COLORS["danger"])

    def _get_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a user first")
            return None
        return self.tree.item(sel[0])["values"]

    def _add_user(self):
        self._user_dialog()

    def _edit_user(self):
        vals = self._get_selected()
        if not vals:
            return
        user = self.model.get_by_id(vals[0])
        if user:
            self._user_dialog(user)

    def _user_dialog(self, user=None):
        dlg = tk.Toplevel(self)
        dlg.title("Edit User" if user else "Add User")
        dlg.geometry("400x380")
        dlg.configure(bg=COLORS["bg_white"])
        dlg.transient(self)
        dlg.grab_set()

        header = tk.Frame(dlg, bg=COLORS["nav_bg"], height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="Edit User" if user else "Add User", font=FONTS["heading"], bg=COLORS["nav_bg"], fg=COLORS["text_white"]).pack(pady=12)

        form = tk.Frame(dlg, bg=COLORS["bg_white"], padx=25, pady=20)
        form.pack(fill="both", expand=True)

        fields = {}
        entry_labels = ["Full Name"]
        if not user:
            entry_labels = ["Username", "Full Name", "Password"]

        for label in entry_labels:
            tk.Label(form, text=label, font=FONTS["small_bold"], bg=COLORS["bg_white"], fg=COLORS["text_primary"]).pack(anchor="w")
            show_val = "*" if "password" in label.lower() else ""
            entry = tk.Entry(form, font=FONTS["body"], bg=COLORS["bg_primary"], fg=COLORS["text_primary"], insertbackground=COLORS["text_primary"], relief="flat", highlightthickness=1, highlightbackground=COLORS["border"], show=show_val)
            entry.pack(pady=(2, 10), ipady=5, fill="x")
            fields[label.lower()] = entry

        if user and "full name" in fields:
            fields["full name"].insert(0, user["full_name"])

        tk.Label(form, text="Role", font=FONTS["small_bold"], bg=COLORS["bg_white"], fg=COLORS["text_primary"]).pack(anchor="w")
        role_var = tk.StringVar(value=user["role"] if user else "attendant")
        role_frame = tk.Frame(form, bg=COLORS["bg_white"])
        role_frame.pack(fill="x", pady=(2, 15))
        for role in ["attendant", "manager", "admin"]:
            tk.Radiobutton(role_frame, text=role.capitalize(), variable=role_var, value=role, font=FONTS["small"], bg=COLORS["bg_white"], fg=COLORS["text_primary"], selectcolor=COLORS["bg_primary"]).pack(side="left", padx=(0, 12))

        def save():
            try:
                if user:
                    self.model.update(user["id"], full_name=fields["full name"].get().strip(), role=role_var.get())
                else:
                    username = fields["username"].get().strip()
                    password = fields["password"].get().strip()
                    full_name = fields["full name"].get().strip()
                    self.model.create(username, password, full_name, role_var.get())
                dlg.destroy()
                self._refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=dlg)

        tk.Button(form, text="Save", font=FONTS["body_bold"], bg=COLORS["nav_bg"], fg=COLORS["text_white"], relief="flat", cursor="hand2", command=save).pack(fill="x", ipady=8)

    def _deactivate_user(self):
        vals = self._get_selected()
        if not vals:
            return
        if vals[3].lower() == "admin":
            messagebox.showwarning("Warning", "Cannot deactivate admin users")
            return
        if messagebox.askyesno("Deactivate", f"Deactivate user '{vals[2]}'?"):
            self.model.delete(vals[0])
            self._refresh()

    def _change_password(self):
        vals = self._get_selected()
        if not vals:
            return
        dlg = tk.Toplevel(self)
        dlg.title("Change Password")
        dlg.geometry("350x180")
        dlg.configure(bg=COLORS["bg_white"])
        dlg.transient(self)
        dlg.grab_set()

        header = tk.Frame(dlg, bg=COLORS["nav_bg"], height=44)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="Change Password", font=FONTS["subheading"], bg=COLORS["nav_bg"], fg=COLORS["text_white"]).pack(pady=10)

        form = tk.Frame(dlg, bg=COLORS["bg_white"], padx=20, pady=15)
        form.pack(fill="both", expand=True)

        tk.Label(form, text=f"New Password for {vals[2]}", font=FONTS["body"], bg=COLORS["bg_white"], fg=COLORS["text_primary"]).pack(anchor="w", pady=(0, 8))
        pwd_var = tk.StringVar()
        tk.Entry(form, textvariable=pwd_var, font=FONTS["body"], bg=COLORS["bg_primary"], fg=COLORS["text_primary"], insertbackground=COLORS["text_primary"], relief="flat", show="*", highlightthickness=1, highlightbackground=COLORS["border"]).pack(fill="x", ipady=5)

        def save():
            try:
                self.model.change_password(vals[0], pwd_var.get())
                dlg.destroy()
                messagebox.showinfo("Success", "Password updated")
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=dlg)

        tk.Button(form, text="Update", font=FONTS["body_bold"], bg=COLORS["nav_bg"], fg=COLORS["text_white"], relief="flat", cursor="hand2", command=save).pack(fill="x", pady=(8, 0), ipady=6)


from config import APP_NAME
