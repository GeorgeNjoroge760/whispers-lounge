from models.product import ProductModel


class ProductController:
    def __init__(self, db):
        self.model = ProductModel(db)

    def get_all_products(self, category_id=None):
        return self.model.get_all(active_only=True, category_id=category_id)

    def get_product(self, product_id):
        return self.model.get_by_id(product_id)

    def add_product(self, name, category_id, price, cost, unit='', barcode=None):
        return self.model.create(name, category_id, price, cost, unit, barcode)

    def edit_product(self, product_id, **kwargs):
        self.model.update(product_id, **kwargs)

    def remove_product(self, product_id):
        self.model.delete(product_id)

    def search_products(self, query):
        return self.model.search(query)

    def get_categories(self):
        return self.model.get_categories()

    def add_category(self, name):
        self.model.add_category(name)

    def remove_category(self, cat_id):
        self.model.delete_category(cat_id)
