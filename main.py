import tkinter as tk
from tkinter import ttk
from database.db import Database
from controllers.auth import AuthController
from controllers.product_ctrl import ProductController
from controllers.sales_ctrl import SalesController
from controllers.inventory_ctrl import InventoryController
from controllers.report_ctrl import ReportController
from utils.theme import COLORS, FONTS, SIZES, configure_ttk_styles
from config import APP_NAME


class WhispersLoungeApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry(f"{SIZES['window_width']}x{SIZES['window_height']}")
        self.root.configure(bg=COLORS["bg_primary"])
        self.root.minsize(1024, 600)

        style = ttk.Style()
        configure_ttk_styles(style)

        self.db = Database()
        self.auth = AuthController(self.db)
        self.product_ctrl = ProductController(self.db)
        self.sales_ctrl = SalesController(self.db)
        self.inventory_ctrl = InventoryController(self.db)
        self.report_ctrl = ReportController(self.db)

        self.current_view = None
        self.navigate("staff_select")

        self.root.mainloop()

    def navigate(self, view_name):
        if self.current_view:
            self.current_view.destroy()

        if view_name == "staff_select":
            from views.login import StaffSelectView
            self.current_view = StaffSelectView(self.root, self.auth, lambda: self.navigate("pos"), lambda: self.navigate("admin_login"))
        elif view_name == "admin_login":
            from views.admin_login import AdminLoginView
            self.current_view = AdminLoginView(self.root, self.auth, lambda: self.navigate("dashboard"), lambda: self.navigate("staff_select"))
        elif view_name == "pos":
            from views.pos_terminal import POSTerminalView
            self.current_view = POSTerminalView(self.root, self.sales_ctrl, self.product_ctrl, self.auth, self.navigate)
        elif view_name == "dashboard":
            from views.dashboard import DashboardView
            self.current_view = DashboardView(self.root, self.auth, self.report_ctrl, self.navigate)
        elif view_name == "catalog":
            from views.product_catalog import ProductCatalogView
            self.current_view = ProductCatalogView(self.root, self.product_ctrl, self.navigate)
        elif view_name == "inventory":
            from views.inventory_view import InventoryView
            self.current_view = InventoryView(self.root, self.inventory_ctrl, self.navigate)
        elif view_name == "reports":
            from views.reports import ReportsView
            self.current_view = ReportsView(self.root, self.report_ctrl, self.navigate)
        elif view_name == "discounts":
            from views.discounts import DiscountsView
            self.current_view = DiscountsView(self.root, self.db, self.navigate)
        elif view_name == "users":
            from views.users import UsersView
            self.current_view = UsersView(self.root, self.db, self.navigate)

        self.current_view.pack(fill="both", expand=True)


if __name__ == "__main__":
    WhispersLoungeApp()
