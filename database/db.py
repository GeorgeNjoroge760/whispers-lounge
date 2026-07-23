import sqlite3
import os
from config import DATABASE_PATH, DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD, DEFAULT_STAFF, RECEIPTS_DIR


class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._create_tables()
        self._seed_data()
        os.makedirs(RECEIPTS_DIR, exist_ok=True)

    def _create_tables(self):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
        with open(schema_path, "r") as f:
            self.conn.executescript(f.read())
        self.conn.commit()

    def _seed_data(self):
        import bcrypt
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            pwd_hash = bcrypt.hashpw(DEFAULT_ADMIN_PASSWORD.encode(), bcrypt.gensalt()).decode()
            cursor.execute(
                "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
                (DEFAULT_ADMIN_USERNAME, pwd_hash, "System Admin", "admin"),
            )
            for staff in DEFAULT_STAFF:
                staff_hash = bcrypt.hashpw(staff["password"].encode(), bcrypt.gensalt()).decode()
                cursor.execute(
                    "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
                    (staff["username"], staff_hash, staff["full_name"], staff["role"]),
                )
        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            cats = [
                ("Spirits", 1), ("Beer", 2), ("Wine", 3), ("Cocktails", 4),
                ("Soft Drinks", 5), ("Shisha", 6), ("Food", 7),
            ]
            cursor.executemany("INSERT INTO categories (name, sort_order) VALUES (?, ?)", cats)
        self.conn.commit()

    def execute(self, query, params=None):
        if params is None:
            params = ()
        cursor = self.conn.execute(query, params)
        self.conn.commit()
        return cursor

    def fetchone(self, query, params=None):
        if params is None:
            params = ()
        return self.conn.execute(query, params).fetchone()

    def fetchall(self, query, params=None):
        if params is None:
            params = ()
        return self.conn.execute(query, params).fetchall()

    def close(self):
        self.conn.close()
