class DiscountModel:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        return self.db.fetchall("SELECT * FROM discounts ORDER BY created_at DESC" if False else "SELECT * FROM discounts ORDER BY id DESC")

    def get_by_code(self, code):
        return self.db.fetchone(
            "SELECT * FROM discounts WHERE code = ? AND is_active = 1 AND (valid_until IS NULL OR valid_until >= DATE('now'))",
            (code,),
        )

    def create(self, code, discount_type, value, min_purchase=0.0, valid_until=None):
        if discount_type not in ("percentage", "fixed"):
            raise ValueError("Type must be 'percentage' or 'fixed'")
        if discount_type == "percentage" and (value <= 0 or value > 100):
            raise ValueError("Percentage must be between 0 and 100")
        if value < 0:
            raise ValueError("Value cannot be negative")
        self.db.execute(
            "INSERT INTO discounts (code, discount_type, value, min_purchase, valid_until) VALUES (?, ?, ?, ?, ?)",
            (code.upper(), discount_type, value, min_purchase, valid_until),
        )

    def update(self, discount_id, **kwargs):
        fields, vals = [], []
        for k, v in kwargs.items():
            if v is not None:
                fields.append(f"{k} = ?")
                vals.append(v)
        if not fields:
            return
        vals.append(discount_id)
        self.db.execute(f"UPDATE discounts SET {', '.join(fields)} WHERE id = ?", tuple(vals))

    def delete(self, discount_id):
        self.db.execute("UPDATE discounts SET is_active = 0 WHERE id = ?", (discount_id,))

    def calculate_discount(self, code, subtotal):
        disc = self.get_by_code(code)
        if not disc:
            return 0, "Invalid or expired discount code"
        if subtotal < disc["min_purchase"]:
            return 0, f"Minimum purchase of ${disc['min_purchase']:.2f} required"
        if disc["discount_type"] == "percentage":
            return subtotal * (disc["value"] / 100), f"{disc['value']}% off"
        return min(disc["value"], subtotal), f"${disc['value']:.2f} off"
