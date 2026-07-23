import os
import sys

APP_NAME = "Whispers Lounge"
APP_VERSION = "1.0.0"

if sys.platform == "android":
    from android.storage import app_storage_path
    BASE_DIR = app_storage_path()
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_PATH = os.path.join(BASE_DIR, "whispers_lounge.db")
RECEIPTS_DIR = os.path.join(BASE_DIR, "receipts")

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"

DEFAULT_STAFF = [
    {"username": "alice", "password": "alice123", "full_name": "Alice", "role": "attendant"},
    {"username": "bob", "password": "bob123", "full_name": "Bob", "role": "attendant"},
]

ROLES = {
    "admin": {"label": "Admin", "level": 3},
    "manager": {"label": "Manager", "level": 2},
    "attendant": {"label": "Attendant", "level": 1},
}

PAYMENT_METHODS = ["Cash", "Card", "Mobile"]

LOW_STOCK_THRESHOLD = 5

COLORS = {
    "nav_bg": "#166534",
    "nav_dark": "#14532d",
    "accent": "#e2a526",
    "accent_hover": "#f0b832",
    "bg_primary": "#f5f5f0",
    "bg_cream": "#faf8f3",
    "bg_white": "#ffffff",
    "bg_card": "#ffffff",
    "success": "#27ae60",
    "danger": "#dc3545",
    "text_primary": "#222222",
    "text_muted": "#888888",
    "text_white": "#ffffff",
    "text_dark": "#000000",
    "border": "#e0e0e0",
    "stock_ok": "#27ae60",
    "stock_low": "#dc3545",
    "stock_zero": "#888888",
}
