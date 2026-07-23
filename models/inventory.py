from config import LOW_STOCK_THRESHOLD


class InventoryModel:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        return self.db.fetchall(
            """SELECT i.*, p.name as product_name, p.is_active
               FROM inventory i JOIN products p ON i.product_id = p.id
               ORDER BY p.name"""
        )

    def get_low_stock(self):
        return self.db.fetchall(
            """SELECT i.*, p.name as product_name
               FROM inventory i JOIN products p ON i.product_id = p.id
               WHERE i.stock_qty <= i.min_stock_level AND p.is_active = 1
               ORDER BY i.stock_qty ASC"""
        )

    def update_stock(self, product_id, qty):
        self.db.execute(
            "UPDATE inventory SET stock_qty = ?, last_restocked = CURRENT_TIMESTAMP WHERE product_id = ?",
            (qty, product_id),
        )

    def add_stock(self, product_id, qty):
        self.db.execute(
            "UPDATE inventory SET stock_qty = stock_qty + ?, last_restocked = CURRENT_TIMESTAMP WHERE product_id = ?",
            (qty, product_id),
        )

    def set_min_level(self, product_id, min_level):
        self.db.execute("UPDATE inventory SET min_stock_level = ? WHERE product_id = ?", (min_level, product_id))

    def get_stock(self, product_id):
        row = self.db.fetchone("SELECT stock_qty FROM inventory WHERE product_id = ?", (product_id,))
        return row["stock_qty"] if row else 0
