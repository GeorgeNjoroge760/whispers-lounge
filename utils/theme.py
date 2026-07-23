COLORS = {
    "bg_primary": "#f5f5f0",
    "bg_cream": "#faf8f3",
    "bg_white": "#ffffff",
    "bg_card": "#ffffff",
    "nav_bg": "#166534",
    "accent": "#e2a526",
    "accent_hover": "#f0b832",
    "success": "#27ae60",
    "danger": "#dc3545",
    "info": "#0dcaf0",
    "text_primary": "#222222",
    "text_muted": "#888888",
    "text_white": "#ffffff",
    "text_dark": "#000000",
    "border": "#e0e0e0",
    "border_light": "#f0f0f0",
    "stock_ok": "#27ae60",
    "stock_low": "#dc3545",
    "stock_zero": "#888888",
    "input_border": "#ced4da",
}

FONTS = {
    "title": ("Segoe UI", 36, "bold"),
    "title_green": ("Segoe UI", 28, "bold"),
    "heading": ("Segoe UI", 16, "bold"),
    "subheading": ("Segoe UI", 13, "bold"),
    "body": ("Segoe UI", 11),
    "body_bold": ("Segoe UI", 11, "bold"),
    "small": ("Segoe UI", 10),
    "small_bold": ("Segoe UI", 10, "bold"),
    "tiny": ("Segoe UI", 8),
    "staff_name": ("Segoe UI", 20, "bold"),
    "product_name": ("Segoe UI", 10, "bold"),
    "product_price": ("Segoe UI", 13, "bold"),
    "product_stock": ("Segoe UI", 8),
    "cart_item": ("Segoe UI", 11),
    "cart_price": ("Consolas", 12, "bold"),
    "big_total": ("Consolas", 18, "bold"),
    "navbar": ("Segoe UI", 14, "bold"),
    "cat_btn": ("Segoe UI", 9),
    "mono": ("Consolas", 11),
    "mono_bold": ("Consolas", 11, "bold"),
}

SIZES = {
    "window_width": 1280,
    "window_height": 720,
    "navbar_height": 56,
    "product_cols": 5,
    "product_min_w": 140,
    "product_min_h": 85,
    "cart_width": 350,
    "cat_bar_height": 44,
    "receipt_width": 42,
    "btn_radius": 12,
    "card_radius": 16,
}


def configure_ttk_styles(style):
    style.theme_use("clam")

    style.configure(".", background=COLORS["bg_primary"], foreground=COLORS["text_primary"], font=FONTS["body"])
    style.configure("TFrame", background=COLORS["bg_primary"])
    style.configure("TLabel", background=COLORS["bg_primary"], foreground=COLORS["text_primary"], font=FONTS["body"])
    style.configure("TButton", background=COLORS["nav_bg"], foreground=COLORS["text_white"], font=FONTS["body_bold"], borderwidth=0, padding=(12, 6))
    style.map("TButton", background=[("active", COLORS["accent"]), ("disabled", COLORS["border"])], foreground=[("active", COLORS["text_dark"])])

    style.configure("White.TFrame", background=COLORS["bg_white"])
    style.configure("White.TLabel", background=COLORS["bg_white"], foreground=COLORS["text_primary"])

    style.configure("Nav.TFrame", background=COLORS["nav_bg"])
    style.configure("Nav.TLabel", background=COLORS["nav_bg"], foreground=COLORS["text_white"])

    style.configure("Card.TFrame", background=COLORS["bg_card"])
    style.configure("Card.TLabel", background=COLORS["bg_card"], foreground=COLORS["text_primary"])

    style.configure("Cream.TFrame", background=COLORS["bg_cream"])
    style.configure("Cream.TLabel", background=COLORS["bg_cream"], foreground=COLORS["text_primary"])

    style.configure("TEntry", fieldbackground=COLORS["bg_white"], foreground=COLORS["text_primary"], insertcolor=COLORS["text_primary"], borderwidth=1, relief="flat")
    style.configure("TCombobox", fieldbackground=COLORS["bg_white"], foreground=COLORS["text_primary"], selectbackground=COLORS["accent"])

    style.configure("Treeview", background=COLORS["bg_white"], foreground=COLORS["text_primary"], fieldbackground=COLORS["bg_white"], borderwidth=0, font=FONTS["body"], rowheight=32)
    style.configure("Treeview.Heading", background=COLORS["bg_cream"], foreground=COLORS["nav_bg"], font=FONTS["body_bold"], borderwidth=0)
    style.map("Treeview", background=[("selected", COLORS["accent"])], foreground=[("selected", COLORS["text_dark"])])
    style.map("Treeview.Heading", background=[("active", COLORS["bg_primary"])])

    style.configure("Green.TButton", background=COLORS["nav_bg"], foreground=COLORS["text_white"])
    style.map("Green.TButton", background=[("active", "#14532d")])
    style.configure("Gold.TButton", background=COLORS["accent"], foreground=COLORS["text_dark"])
    style.map("Gold.TButton", background=[("active", COLORS["accent_hover"])])
    style.configure("Danger.TButton", background=COLORS["danger"], foreground=COLORS["text_white"])
    style.map("Danger.TButton", background=[("active", "#bb2d3b")])
    style.configure("Success.TButton", background=COLORS["success"], foreground=COLORS["text_white"])
    style.map("Success.TButton", background=[("active", "#1e8449")])
    style.configure("Outline.TButton", background=COLORS["bg_white"], foreground=COLORS["nav_bg"], borderwidth=2)
    style.map("Outline.TButton", background=[("active", COLORS["nav_bg"])], foreground=[("active", COLORS["text_white"])])

    style.configure("Horizontal.TProgressbar", background=COLORS["accent"], troughcolor=COLORS["border_light"], borderwidth=0)
