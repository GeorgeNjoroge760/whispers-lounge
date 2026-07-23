from utils.validators import Validators


class ProductModel:
    def __init__(self, db):
        self.db = db

    def get_all(self, active_only=False, category_id=None):
        q = """SELECT p.*, c.name as category_name, i.stock_qty
               FROM products p
               LEFT JOIN categories c ON p.category_id = c.id
               LEFT JOIN inventory i ON p.id = i.product_id"""
        conditions, params = [], []
        if active_only:
            conditions.append("p.is_active = 1")
        if category_id:
            conditions.append("p.category_id = ?")
            params.append(category_id)
        if conditions:
            q += " WHERE " + " AND ".join(conditions)
        q += " ORDER BY p.name"
        return self.db.fetchall(q, tuple(params))

    def get_by_id(self, product_id):
        return self.db.fetchone(
            """SELECT p.*, c.name as category_name, i.stock_qty
               FROM products p
               LEFT JOIN categories c ON p.category_id = c.id
               LEFT JOIN inventory i ON p.id = i.product_id
               WHERE p.id = ?""",
            (product_id,),
        )

    def get_categories(self):
        return self.db.fetchall("SELECT * FROM categories ORDER BY sort_order")

    def create(self, name, category_id, price, cost, unit='', barcode=None):
        Validators.not_empty(name, "Product name")
        Validators.positive_number(price, "Price")
        Validators.positive_number(cost, "Cost", allow_zero=True)
        product_id = self.db.execute(
            "INSERT INTO products (name, category_id, price, cost, unit, barcode) VALUES (?, ?, ?, ?, ?, ?)",
            (name, category_id, price, cost, unit, barcode),
        ).lastrowid
        self.db.execute(
            "INSERT INTO inventory (product_id, stock_qty, min_stock_level) VALUES (?, 0, 5)",
            (product_id,),
        )
        return product_id

    def update(self, product_id, name=None, category_id=None, price=None, cost=None, unit=None, barcode=None, stock_qty=None):
        fields, vals = [], []
        if name is not None:
            fields.append("name = ?")
            vals.append(name)
        if category_id is not None:
            fields.append("category_id = ?")
            vals.append(category_id)
        if price is not None:
            fields.append("price = ?")
            vals.append(price)
        if cost is not None:
            fields.append("cost = ?")
            vals.append(cost)
        if unit is not None:
            fields.append("unit = ?")
            vals.append(unit)
        if barcode is not None:
            fields.append("barcode = ?")
            vals.append(barcode)
        if not fields:
            return
        vals.append(product_id)
        self.db.execute(f"UPDATE products SET {', '.join(fields)} WHERE id = ?", tuple(vals))
        if stock_qty is not None:
            self.db.execute(
                "UPDATE inventory SET stock_qty = ? WHERE product_id = ?",
                (stock_qty, product_id),
            )

    def delete(self, product_id):
        self.db.execute("UPDATE products SET is_active = 0 WHERE id = ?", (product_id,))

    def search(self, query):
        return self.db.fetchall(
            """SELECT p.*, c.name as category_name, i.stock_qty
               FROM products p
               LEFT JOIN categories c ON p.category_id = c.id
               LEFT JOIN inventory i ON p.id = i.product_id
               WHERE p.is_active = 1 AND (p.name LIKE ? OR p.barcode LIKE ?)
               ORDER BY p.name""",
            (f"%{query}%", f"%{query}%"),
        )

    def add_category(self, name):
        Validators.not_empty(name, "Category name")
        self.db.execute("INSERT INTO categories (name) VALUES (?)", (name,))

    def delete_category(self, cat_id):
        self.db.execute("UPDATE products SET category_id = NULL WHERE category_id = ?", (cat_id,))
        self.db.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
