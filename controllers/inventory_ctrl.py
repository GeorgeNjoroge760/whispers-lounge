from models.inventory import InventoryModel


class InventoryController:
    def __init__(self, db):
        self.model = InventoryModel(db)

    def get_all_stock(self):
        return self.model.get_all()

    def get_low_stock(self):
        return self.model.get_low_stock()

    def restock_product(self, product_id, qty):
        if qty <= 0:
            raise ValueError("Quantity must be positive")
        self.model.add_stock(product_id, qty)

    def set_stock(self, product_id, qty):
        if qty < 0:
            raise ValueError("Stock cannot be negative")
        self.model.update_stock(product_id, qty)

    def set_min_level(self, product_id, level):
        if level < 0:
            raise ValueError("Minimum level cannot be negative")
        self.model.set_min_level(product_id, level)

    def get_stock_level(self, product_id):
        return self.model.get_stock(product_id)
