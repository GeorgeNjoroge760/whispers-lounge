from datetime import datetime, timedelta
from models.sale import SaleModel


class ReportController:
    def __init__(self, db):
        self.model = SaleModel(db)

    def get_today_summary(self):
        today = datetime.now().strftime("%Y-%m-%d")
        return self.model.get_daily_summary(today)

    def get_sales(self, start_date=None, end_date=None):
        return self.model.get_sales(start_date, end_date)

    def get_top_products(self, limit=10, start_date=None, end_date=None):
        return self.model.get_top_products(limit, start_date, end_date)

    def get_sales_by_category(self, start_date=None, end_date=None):
        return self.model.get_sales_by_category(start_date, end_date)

    def get_sales_chart_data(self, days=7):
        return self.model.get_sales_by_date_range(days)

    def get_date_range(self, period="today"):
        now = datetime.now()
        if period == "today":
            return now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")
        elif period == "yesterday":
            d = now - timedelta(days=1)
            return d.strftime("%Y-%m-%d"), d.strftime("%Y-%m-%d")
        elif period == "week":
            start = now - timedelta(days=now.weekday())
            return start.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")
        elif period == "month":
            start = now.replace(day=1)
            return start.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")
        elif period == "year":
            start = now.replace(month=1, day=1)
            return start.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")
        return None, None
