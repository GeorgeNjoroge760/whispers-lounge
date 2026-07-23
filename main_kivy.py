import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty, ListProperty

from database.db import Database
from controllers.auth import AuthController
from controllers.product_ctrl import ProductController
from controllers.sales_ctrl import SalesController
from controllers.inventory_ctrl import InventoryController
from controllers.report_ctrl import ReportController
from config import APP_NAME


db = Database()
auth_ctrl = AuthController(db)
product_ctrl = ProductController(db)
sales_ctrl = SalesController(db)
inventory_ctrl = InventoryController(db)
report_ctrl = ReportController(db)


class StaffSelectScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self._build_staff, 0.1)

    def _build_staff(self, dt):
        grid = self.ids.staff_grid
        grid.clear_widgets()
        staff = auth_ctrl.get_all_staff()
        grid.cols = min(len(staff), 2)
        for user in staff:
            btn = Button(
                text=f"{user['full_name']}\n\u00b7 {user['role'].capitalize()}",
                font_size=dp(20),
                bold=True,
                size_hint_y=None,
                height=dp(110),
                background_color=(1, 1, 1, 1),
                background_normal='',
                color=(0.086, 0.396, 0.204, 1),
            )
            btn.bind(on_press=lambda inst, u=user: self.select_staff(u))
            grid.add_widget(btn)

    def select_staff(self, user):
        auth_ctrl.set_current_user(user)
        self.manager.get_screen('pos').setup_pos()
        self.manager.current = 'pos'

    def go_admin_login(self):
        self.manager.current = 'admin_login'


class AdminLoginScreen(Screen):
    def do_login(self):
        username = self.ids.admin_user.text.strip()
        password = self.ids.admin_pass.text.strip()
        if not username or not password:
            self.ids.admin_error.text = "Please enter username and password"
            return
        success, msg = auth_ctrl.login(username, password)
        if success:
            self.ids.admin_error.text = ""
            self.ids.admin_user.text = ""
            self.ids.admin_pass.text = ""
            self.manager.get_screen('dashboard').refresh_data()
            self.manager.current = 'dashboard'
        else:
            self.ids.admin_error.text = msg
            self.ids.admin_pass.text = ""

    def go_back(self):
        self.ids.admin_user.text = ""
        self.ids.admin_pass.text = ""
        self.ids.admin_error.text = ""
        self.manager.current = 'staff_select'


class PosScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_category = None
        self.payment_method = 'Cash'

    def setup_pos(self):
        user = auth_ctrl.get_current_user()
        if user:
            self.ids.pos_user_label.text = f"\U0001f464 {user['full_name']}"
        self._build_categories()
        self.filter_products()
        self.refresh_cart()

    def _build_categories(self):
        bar = self.ids.cat_bar
        bar.clear_widgets()
        btn = ToggleButton(text='All', group='category', state='down', font_size=dp(12),
                           size_hint=(None, None), size=(dp(60), dp(32)),
                           background_color=(0.886, 0.647, 0.149, 1), color=(0, 0, 0, 1),
                           on_press=lambda x: self.select_category(None))
        bar.add_widget(btn)
        for cat in product_ctrl.get_categories():
            btn = ToggleButton(text=cat['name'], group='category', font_size=dp(12),
                               size_hint=(None, None), size=(dp(100), dp(32)),
                               background_color=(1, 1, 1, 1), background_normal=(1, 1, 1, 1),
                               color=(0.133, 0.133, 0.133, 1),
                               on_press=lambda x, cid=cat['id']: self.select_category(cid))
            bar.add_widget(btn)

    def select_category(self, cat_id):
        self.selected_category = cat_id
        self.filter_products()

    def filter_products(self):
        query = self.ids.search_input.text.strip()
        if query:
            products = product_ctrl.search_products(query)
        else:
            products = product_ctrl.get_all_products(category_id=self.selected_category)
        self._display_products(products)

    def _display_products(self, products):
        grid = self.ids.product_grid
        grid.clear_widgets()
        grid.cols = 3
        for p in products:
            stock = p['stock_qty'] if p['stock_qty'] is not None else 0
            stock_color = (0.533, 0.533, 0.533, 1) if stock <= 0 else (0.863, 0.208, 0.271, 1) if stock <= 5 else (0.153, 0.682, 0.376, 1)
            btn = Button(
                text=f"{p['name']}\n${p['price']:.2f}\nStock: {stock}",
                font_size=dp(11),
                bold=False,
                size_hint_y=None,
                height=dp(90),
                background_color=(1, 1, 1, 1),
                background_normal='',
                color=(0.133, 0.133, 0.133, 1),
            )
            btn.bind(on_press=lambda inst, prod=p: self.add_to_cart(prod))
            grid.add_widget(btn)

    def add_to_cart(self, product):
        stock = product['stock_qty'] if product['stock_qty'] is not None else 0
        if stock <= 0:
            self._show_popup("Out of Stock", f"{product['name']} is out of stock!")
            return
        sales_ctrl.add_to_cart(product)
        self.refresh_cart()

    def refresh_cart(self):
        cart_list = self.ids.cart_list
        cart_list.clear_widgets()
        cart = sales_ctrl.get_cart()
        if not cart:
            lbl = Label(text='Cart is empty', font_size=dp(12), color=(0.533, 0.533, 0.533, 1),
                        size_hint_y=None, height=dp(40))
            cart_list.add_widget(lbl)
        else:
            for i, item in enumerate(cart):
                row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(44),
                                padding=[dp(10), dp(4)])
                row.add_widget(Label(text=f"{item['name']} x{item['qty']}", font_size=dp(12),
                                     halign='left', text_size=(dp(180), None), color=(0.133, 0.133, 0.133, 1)))
                row.add_widget(Label(text=f"${item['subtotal']:.2f}", font_size=dp(13), bold=True,
                                     color=(0.086, 0.396, 0.204, 1)))
                minus_btn = Button(text='-', size_hint=(None, None), size=(dp(30), dp(30)),
                                   font_size=dp(14), background_color=(0.961, 0.961, 0.941, 1),
                                   background_normal='', color=(0.133, 0.133, 0.133, 1))
                minus_btn.bind(on_press=lambda inst, idx=i: self.change_qty(idx, -1))
                row.add_widget(minus_btn)
                plus_btn = Button(text='+', size_hint=(None, None), size=(dp(30), dp(30)),
                                  font_size=dp(14), background_color=(0.961, 0.961, 0.941, 1),
                                  background_normal='', color=(0.133, 0.133, 0.133, 1))
                plus_btn.bind(on_press=lambda inst, idx=i: self.change_qty(idx, 1))
                row.add_widget(plus_btn)
                cart_list.add_widget(row)

        self.ids.subtotal_label.text = f"Subtotal: ${sales_ctrl.get_cart_subtotal():.2f}"
        self.ids.total_label.text = f"TOTAL: ${sales_ctrl.get_cart_total():.2f}"

    def change_qty(self, idx, delta):
        cart = sales_ctrl.get_cart()
        new_qty = cart[idx]['qty'] + delta
        sales_ctrl.update_cart_qty(idx, new_qty)
        self.refresh_cart()

    def set_payment(self, method):
        self.payment_method = method

    def apply_discount(self):
        code = self.ids.disc_input.text.strip()
        if not code:
            return
        ok, msg = sales_ctrl.apply_discount(code)
        self.ids.disc_label.text = msg
        self.refresh_cart()

    def complete_sale(self):
        cart = sales_ctrl.get_cart()
        if not cart:
            self._show_popup("Empty Cart", "Add items to the cart first!")
            return
        total = sales_ctrl.get_cart_total()
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(12))
        content.add_widget(Label(text=f'Total: ${total:.2f}\nPayment: {self.payment_method}',
                                 font_size=dp(16), halign='center'))
        btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        cancel_btn = Button(text='Cancel', background_color=(0.863, 0.208, 0.271, 1),
                            background_normal='', color=(1, 1, 1, 1))
        confirm_btn = Button(text='Confirm Sale', background_color=(0.086, 0.396, 0.204, 1),
                             background_normal='', color=(1, 1, 1, 1))
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(confirm_btn)
        content.add_widget(btn_row)

        popup = Popup(title='Complete Sale', content=content, size_hint=(0.85, 0.4), auto_dismiss=False)
        cancel_btn.bind(on_press=popup.dismiss)
        confirm_btn.bind(on_press=lambda x: self._do_sale(popup))
        popup.open()

    def _do_sale(self, popup):
        popup.dismiss()
        try:
            user = auth_ctrl.get_current_user()
            sale_id, receipt_path, receipt_text = sales_ctrl.finalize_sale(user['id'], self.payment_method)
            self.ids.disc_input.text = ""
            self.ids.disc_label.text = ""
            self.refresh_cart()
            self.filter_products()
            self._show_receipt(sale_id, receipt_text)
        except Exception as e:
            self._show_popup("Error", str(e))

    def _show_receipt(self, sale_id, receipt_text):
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        content.add_widget(Label(text=f'Sale #{sale_id} Complete!', font_size=dp(16), bold=True,
                                 color=(0.153, 0.682, 0.376, 1)))
        scroll = ScrollView()
        lbl = Label(text=receipt_text, font_size=dp(11), size_hint_y=None, halign='left',
                    text_size=(dp(300), None), color=(0.133, 0.133, 0.133, 1))
        lbl.bind(texture_size=lbl.setter('size'))
        scroll.add_widget(lbl)
        content.add_widget(scroll)
        close_btn = Button(text='Close', size_hint_y=None, height=dp(40),
                           background_color=(0.086, 0.396, 0.204, 1), background_normal='', color=(1, 1, 1, 1))
        content.add_widget(close_btn)
        popup = Popup(title='Receipt', content=content, size_hint=(0.9, 0.7))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

    def _show_popup(self, title, msg):
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(12))
        content.add_widget(Label(text=msg, font_size=dp(14), halign='center'))
        btn = Button(text='OK', size_hint_y=None, height=dp(40),
                     background_color=(0.086, 0.396, 0.204, 1), background_normal='', color=(1, 1, 1, 1))
        content.add_widget(btn)
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.35))
        btn.bind(on_press=popup.dismiss)
        popup.open()

    def logout(self):
        sales_ctrl.clear_cart()
        auth_ctrl.logout()
        self.manager.current = 'staff_select'


class DashboardScreen(Screen):
    def refresh_data(self):
        summary = report_ctrl.get_today_summary()
        self.ids.revenue_label.text = f"${summary['revenue']:.2f}"
        self.ids.tx_label.text = str(summary['total_sales'])
        self.ids.disc_total_label.text = f"${summary['discounts']:.2f}"
        low = inventory_ctrl.get_low_stock()
        self.ids.low_stock_label.text = str(len(low))

    def go_pos(self):
        self.manager.get_screen('pos').setup_pos()
        self.manager.current = 'pos'

    def go_catalog(self):
        self.manager.get_screen('catalog').load_data()
        self.manager.current = 'catalog'

    def go_inventory(self):
        self.manager.get_screen('inventory').load_data()
        self.manager.current = 'inventory'

    def go_reports(self):
        self.manager.get_screen('reports').load_data()
        self.manager.current = 'reports'

    def go_discounts(self):
        self.manager.get_screen('discounts').load_data()
        self.manager.current = 'discounts'

    def go_users(self):
        self.manager.get_screen('users').load_data()
        self.manager.current = 'users'


class GenericListScreen(Screen):
    screen_title = StringProperty("")
    data_items = ListProperty([])
    selected_index = -1

    def go_back(self):
        self.manager.current = 'dashboard'

    def on_action1(self):
        pass

    def on_action2(self):
        pass

    def on_search(self):
        pass


class CatalogScreen(GenericListScreen):
    def load_data(self):
        self.screen_title = "Product Catalog"
        self.ids.action_btn1.text = "+ Add Product"
        self.ids.action_btn2.text = "Delete"
        self.refresh_list()

    def refresh_list(self):
        lst = self.ids.item_list
        lst.clear_widgets()
        for p in product_ctrl.get_all_products():
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(44), padding=[dp(14), dp(6)])
            stock = p['stock_qty'] if p['stock_qty'] is not None else 'N/A'
            row.add_widget(Label(text=p['name'], font_size=dp(13), halign='left', text_size=(dp(200), None),
                                 color=(0.133, 0.133, 0.133, 1)))
            row.add_widget(Label(text=p['category_name'] or '-', font_size=dp(12),
                                 color=(0.533, 0.533, 0.533, 1)))
            row.add_widget(Label(text=f"${p['price']:.2f}", font_size=dp(13), bold=True,
                                 color=(0.086, 0.396, 0.204, 1)))
            lst.add_widget(row)


class InventoryScreen(GenericListScreen):
    def load_data(self):
        self.screen_title = "Inventory"
        self.ids.action_btn1.text = "Restock"
        self.ids.action_btn2.text = "Low Stock"
        self.refresh_list()

    def refresh_list(self, low_only=False):
        lst = self.ids.item_list
        lst.clear_widgets()
        items = inventory_ctrl.get_low_stock() if low_only else inventory_ctrl.get_all_stock()
        for item in items:
            if not item['is_active']:
                continue
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(44), padding=[dp(14), dp(6)])
            row.add_widget(Label(text=item['product_name'], font_size=dp(13), halign='left',
                                 text_size=(dp(180), None), color=(0.133, 0.133, 0.133, 1)))
            color = (0.863, 0.208, 0.271, 1) if item['stock_qty'] <= item['min_stock_level'] else (0.086, 0.396, 0.204, 1)
            row.add_widget(Label(text=str(item['stock_qty']), font_size=dp(13), bold=True, color=color))
            row.add_widget(Label(text=f"Min: {item['min_stock_level']}", font_size=dp(11),
                                 color=(0.533, 0.533, 0.533, 1)))
            lst.add_widget(row)

    def on_action1(self):
        items = inventory_ctrl.get_all_stock()
        if not items:
            return
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(8))
        names = [f"{i['product_name']} (Stock: {i['stock_qty']})" for i in items if i['is_active']]
        content.add_widget(Label(text='Select product (first match):', font_size=dp(13)))
        content.add_widget(Label(text=names[0] if names else 'No products', font_size=dp(12),
                                 color=(0.533, 0.533, 0.533, 1)))
        qty_input = TextInput(hint_text='Quantity to add', font_size=dp(14), multiline=False,
                              size_hint_y=None, height=dp(40), padding=[dp(8), dp(8)])
        content.add_widget(qty_input)
        btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        cancel = Button(text='Cancel', background_color=(0.863, 0.208, 0.271, 1),
                        background_normal='', color=(1, 1, 1, 1))
        confirm = Button(text='Restock', background_color=(0.086, 0.396, 0.204, 1),
                         background_normal='', color=(1, 1, 1, 1))
        btn_row.add_widget(cancel)
        btn_row.add_widget(confirm)
        content.add_widget(btn_row)
        popup = Popup(title='Restock', content=content, size_hint=(0.85, 0.5), auto_dismiss=False)
        cancel.bind(on_press=popup.dismiss)

        def do_restock(x):
            try:
                qty = int(qty_input.text)
                inventory_ctrl.restock_product(items[0]['product_id'], qty)
                popup.dismiss()
                self.refresh_list()
            except Exception as e:
                pass

        confirm.bind(on_press=do_restock)
        popup.open()

    def on_action2(self):
        self.refresh_list(low_only=True)


class ReportsScreen(GenericListScreen):
    def load_data(self):
        self.screen_title = "Reports"
        self.ids.action_btn1.text = "Today"
        self.ids.action_btn2.text = "This Week"
        self.refresh_list()

    def refresh_list(self, period='today'):
        lst = self.ids.item_list
        lst.clear_widgets()
        start, end = report_ctrl.get_date_range(period)
        summary_items = report_ctrl.get_sales(start, end)
        total_rev = sum(s['total'] for s in summary_items)
        total_disc = sum(s['discount_amount'] for s in summary_items)

        for label, value, color in [
            ("Total Revenue", f"${total_rev:.2f}", (0.086, 0.396, 0.204, 1)),
            ("Transactions", str(len(summary_items)), (0.886, 0.647, 0.149, 1)),
            ("Discounts Given", f"${total_disc:.2f}", (0.863, 0.208, 0.271, 1)),
        ]:
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(48), padding=[dp(14), dp(6)])
            row.add_widget(Label(text=label, font_size=dp(14), halign='left', text_size=(dp(250), None),
                                 color=(0.133, 0.133, 0.133, 1)))
            row.add_widget(Label(text=value, font_size=dp(16), bold=True, color=color))
            lst.add_widget(row)

        top = report_ctrl.get_top_products(10, start, end)
        if top:
            header = BoxLayout(size_hint_y=None, height=dp(36), padding=[dp(14), dp(6)])
            header.add_widget(Label(text='Top Products', font_size=dp(14), bold=True,
                                    color=(0.086, 0.396, 0.204, 1), halign='left',
                                    text_size=(dp(250), None)))
            lst.add_widget(header)
        for p in top:
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(36), padding=[dp(14), dp(2)])
            row.add_widget(Label(text=p['name'], font_size=dp(12), halign='left', text_size=(dp(200), None),
                                 color=(0.133, 0.133, 0.133, 1)))
            row.add_widget(Label(text=f"${p['total_revenue']:.2f}", font_size=dp(12), bold=True,
                                 color=(0.086, 0.396, 0.204, 1)))
            lst.add_widget(row)

    def on_action1(self):
        self.refresh_list('today')

    def on_action2(self):
        self.refresh_list('week')


class DiscountsScreen(GenericListScreen):
    def load_data(self):
        self.screen_title = "Discounts"
        self.ids.action_btn1.text = "+ Add Discount"
        self.ids.action_btn2.text = "Delete"
        self.refresh_list()

    def refresh_list(self):
        from models.discount import DiscountModel
        model = DiscountModel(db)
        lst = self.ids.item_list
        lst.clear_widgets()
        for d in model.get_all():
            val = f"{d['value']}%" if d['discount_type'] == 'percentage' else f"${d['value']:.2f}"
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(44), padding=[dp(14), dp(6)])
            row.add_widget(Label(text=d['code'], font_size=dp(14), bold=True, halign='left',
                                 text_size=(dp(150), None), color=(0.133, 0.133, 0.133, 1)))
            row.add_widget(Label(text=val, font_size=dp(13), color=(0.086, 0.396, 0.204, 1)))
            row.add_widget(Label(text=d['valid_until'] or 'No expiry', font_size=dp(11),
                                 color=(0.533, 0.533, 0.533, 1)))
            lst.add_widget(row)


class UsersScreen(GenericListScreen):
    def load_data(self):
        self.screen_title = "User Management"
        self.ids.action_btn1.text = "+ Add User"
        self.ids.action_btn2.text = "Deactivate"
        self.refresh_list()

    def refresh_list(self):
        lst = self.ids.item_list
        lst.clear_widgets()
        for u in auth_ctrl.get_all_staff():
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(44), padding=[dp(14), dp(6)])
            row.add_widget(Label(text=u['full_name'], font_size=dp(13), halign='left',
                                 text_size=(dp(180), None), color=(0.133, 0.133, 0.133, 1)))
            row.add_widget(Label(text=u['role'].capitalize(), font_size=dp(12),
                                 color=(0.086, 0.396, 0.204, 1)))
            active = "Active" if u['is_active'] else "Inactive"
            acolor = (0.153, 0.682, 0.376, 1) if u['is_active'] else (0.863, 0.208, 0.271, 1)
            row.add_widget(Label(text=active, font_size=dp(11), color=acolor))
            lst.add_widget(row)


class WhispersLoungeApp(App):
    def build(self):
        self.title = APP_NAME
        sm = ScreenManager(transition=SlideTransition(direction='left'))
        sm.add_widget(StaffSelectScreen(name='staff_select'))
        sm.add_widget(AdminLoginScreen(name='admin_login'))
        sm.add_widget(PosScreen(name='pos'))
        sm.add_widget(DashboardScreen(name='dashboard'))
        sm.add_widget(CatalogScreen(name='catalog'))
        sm.add_widget(InventoryScreen(name='inventory'))
        sm.add_widget(ReportsScreen(name='reports'))
        sm.add_widget(DiscountsScreen(name='discounts'))
        sm.add_widget(UsersScreen(name='users'))
        return sm


if __name__ == '__main__':
    WhispersLoungeApp().run()
