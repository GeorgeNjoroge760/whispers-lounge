class SaleModel:
    def __init__(self, db):
        self.db = db

    def create_sale(self, user_id, items, discount_amount=0.0, payment_method="Cash"):
        total = sum(item["subtotal"] for item in items) - discount_amount
        if total < 0:
            total = 0
        sale_id = self.db.execute(
            "INSERT INTO sales (user_id, total, discount_amount, payment_method) VALUES (?, ?, ?, ?)",
            (user_id, total, discount_amount, payment_method),
        ).lastrowid
        for item in items:
            self.db.execute(
                "INSERT INTO sale_items (sale_id, product_id, qty, unit_price, subtotal) VALUES (?, ?, ?, ?, ?)",
                (sale_id, item["product_id"], item["qty"], item["unit_price"], item["subtotal"]),
            )
            self.db.execute(
                "UPDATE inventory SET stock_qty = stock_qty - ? WHERE product_id = ?",
                (item["qty"], item["product_id"]),
            )
        return sale_id

    def get_sale(self, sale_id):
        sale = self.db.fetchone("SELECT s.*, u.full_name as attendant FROM sales s JOIN users u ON s.user_id = u.id WHERE s.id = ?", (sale_id,))
        if sale:
            items = self.db.fetchall(
                """SELECT si.*, p.name as product_name
                   FROM sale_items si JOIN products p ON si.product_id = p.id
                   WHERE si.sale_id = ?""",
                (sale_id,),
            )
            return {"sale": dict(sale), "items": [dict(i) for i in items]}
        return None

    def get_sales(self, start_date=None, end_date=None):
        q = """SELECT s.*, u.full_name as attendant
               FROM sales s JOIN users u ON s.user_id = u.id"""
        conditions, params = [], []
        if start_date:
            conditions.append("s.created_at >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("s.created_at <= ?")
            params.append(end_date + " 23:59:59")
        if conditions:
            q += " WHERE " + " AND ".join(conditions)
        q += " ORDER BY s.created_at DESC"
        return self.db.fetchall(q, tuple(params))

    def get_daily_summary(self, date):
        return self.db.fetchone(
            """SELECT COUNT(*) as total_sales, COALESCE(SUM(total), 0) as revenue,
                      COALESCE(SUM(discount_amount), 0) as discounts
               FROM sales WHERE DATE(created_at) = DATE(?)""",
            (date,),
        )

    def get_top_products(self, limit=10, start_date=None, end_date=None):
        q = """SELECT p.name, SUM(si.qty) as total_qty, SUM(si.subtotal) as total_revenue
               FROM sale_items si JOIN products p ON si.product_id = p.id
               JOIN sales s ON si.sale_id = s.id"""
        conditions, params = [], []
        if start_date:
            conditions.append("s.created_at >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("s.created_at <= ?")
            params.append(end_date + " 23:59:59")
        if conditions:
            q += " WHERE " + " AND ".join(conditions)
        q += " GROUP BY p.id ORDER BY total_revenue DESC LIMIT ?"
        params.append(limit)
        return self.db.fetchall(q, tuple(params))

    def get_sales_by_category(self, start_date=None, end_date=None):
        q = """SELECT c.name, SUM(si.subtotal) as revenue
               FROM sale_items si JOIN products p ON si.product_id = p.id
               JOIN categories c ON p.category_id = c.id
               JOIN sales s ON si.sale_id = s.id"""
        conditions, params = [], []
        if start_date:
            conditions.append("s.created_at >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("s.created_at <= ?")
            params.append(end_date + " 23:59:59")
        if conditions:
            q += " WHERE " + " AND ".join(conditions)
        q += " GROUP BY c.id ORDER BY revenue DESC"
        return self.db.fetchall(q, tuple(params))

    def get_sales_by_date_range(self, days=7):
        return self.db.fetchall(
            """SELECT DATE(s.created_at) as sale_date, COUNT(*) as num_sales, SUM(s.total) as revenue
               FROM sales s
               WHERE s.created_at >= DATE('now', ?)
               GROUP BY DATE(s.created_at) ORDER BY sale_date""",
            (f"-{days} days",),
        )
