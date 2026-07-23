from models.sale import SaleModel
from models.discount import DiscountModel
from utils.receipt import generate_receipt


class SalesController:
    def __init__(self, db):
        self.sale_model = SaleModel(db)
        self.discount_model = DiscountModel(db)
        self.cart = []
        self.applied_discount = None

    def add_to_cart(self, product, qty=1):
        for item in self.cart:
            if item["product_id"] == product["id"]:
                item["qty"] += qty
                item["subtotal"] = item["qty"] * item["unit_price"]
                return self.cart
        self.cart.append({
            "product_id": product["id"],
            "name": product["name"],
            "unit_price": product["price"],
            "qty": qty,
            "subtotal": qty * product["price"],
        })
        return self.cart

    def update_cart_qty(self, index, qty):
        if 0 <= index < len(self.cart):
            if qty <= 0:
                self.cart.pop(index)
            else:
                self.cart[index]["qty"] = qty
                self.cart[index]["subtotal"] = qty * self.cart[index]["unit_price"]

    def remove_from_cart(self, index):
        if 0 <= index < len(self.cart):
            self.cart.pop(index)

    def clear_cart(self):
        self.cart = []
        self.applied_discount = None

    def get_cart(self):
        return self.cart

    def get_cart_subtotal(self):
        return sum(item["subtotal"] for item in self.cart)

    def get_cart_total(self):
        subtotal = self.get_cart_subtotal()
        if self.applied_discount:
            return subtotal - self.applied_discount["amount"]
        return subtotal

    def apply_discount(self, code):
        amount, message = self.discount_model.calculate_discount(code, self.get_cart_subtotal())
        if amount > 0:
            self.applied_discount = {"code": code, "amount": amount, "message": message}
        else:
            self.applied_discount = None
        return amount > 0, message

    def remove_discount(self):
        self.applied_discount = None

    def finalize_sale(self, user_id, payment_method="Cash"):
        if not self.cart:
            raise ValueError("Cart is empty")
        discount_amount = self.applied_discount["amount"] if self.applied_discount else 0
        sale_id = self.sale_model.create_sale(user_id, self.cart, discount_amount, payment_method)
        sale_data = self.sale_model.get_sale(sale_id)
        receipt_path, receipt_text = generate_receipt(sale_data, sale_data["items"])
        self.clear_cart()
        return sale_id, receipt_path, receipt_text
