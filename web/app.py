import os
import sys
import secrets
from flask import Flask, jsonify, request, session, send_from_directory, render_template

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import Database
from controllers.auth import AuthController
from controllers.product_ctrl import ProductController
from controllers.sales_ctrl import SalesController
from controllers.inventory_ctrl import InventoryController
from controllers.report_ctrl import ReportController
from models.discount import DiscountModel
from models.user import UserModel

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_TYPE'] = 'filesystem'

db = Database()
auth_ctrl = AuthController(db)
product_ctrl = ProductController(db)
sales_ctrl = SalesController(db)
inventory_ctrl = InventoryController(db)
report_ctrl = ReportController(db)
discount_model = DiscountModel(db)
user_model = UserModel(db)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')


@app.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js')


@app.route('/api/staff')
def get_staff():
    staff = auth_ctrl.get_all_staff()
    return jsonify(staff)


@app.route('/api/staff/select', methods=['POST'])
def select_staff():
    data = request.json
    user_id = data.get('staff_id')
    user = user_model.get_by_id(user_id)
    if user:
        session['user'] = dict(user)
        session['role'] = user['role']
        return jsonify({'ok': True, 'user': {'id': user['id'], 'name': user['full_name'], 'role': user['role']}})
    return jsonify({'ok': False, 'msg': 'User not found'}), 404


@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    success, msg = auth_ctrl.login(data.get('username', ''), data.get('password', ''))
    if success:
        user = auth_ctrl.get_current_user()
        session['user'] = user
        session['role'] = user['role']
        return jsonify({'ok': True, 'user': {'id': user['id'], 'name': user['full_name'], 'role': user['role']}})
    return jsonify({'ok': False, 'msg': msg})


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    auth_ctrl.logout()
    sales_ctrl.clear_cart()
    return jsonify({'ok': True})


@app.route('/api/products')
def get_products():
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search', '')
    if search:
        products = product_ctrl.search_products(search)
    else:
        products = product_ctrl.get_all_products(category_id=category_id)
    result = []
    for p in products:
        result.append({
            'id': p['id'], 'name': p['name'], 'price': p['price'],
            'cost': p['cost'], 'unit': p['unit'] or '',
            'category_id': p['category_id'],
            'category_name': p['category_name'] or '',
            'stock': p['stock_qty'] if p['stock_qty'] is not None else 0,
            'barcode': p['barcode'] or ''
        })
    return jsonify(result)


@app.route('/api/products', methods=['POST'])
def create_product():
    data = request.json
    try:
        pid = product_ctrl.add_product(
            data['name'], data.get('category_id'),
            float(data['price']), float(data.get('cost', 0)),
            data.get('unit', ''), data.get('barcode')
        )
        return jsonify({'ok': True, 'id': pid})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 400


@app.route('/api/products/<int:pid>', methods=['PUT'])
def update_product(pid):
    data = request.json
    try:
        product_ctrl.edit_product(pid, **data)
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 400


@app.route('/api/products/<int:pid>', methods=['DELETE'])
def delete_product(pid):
    product_ctrl.remove_product(pid)
    return jsonify({'ok': True})


@app.route('/api/categories')
def get_categories():
    cats = product_ctrl.get_categories()
    return jsonify([{'id': c['id'], 'name': c['name']} for c in cats])


@app.route('/api/categories', methods=['POST'])
def create_category():
    data = request.json
    try:
        product_ctrl.add_category(data['name'])
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 400


@app.route('/api/cart/add', methods=['POST'])
def cart_add():
    data = request.json
    product = product_ctrl.get_product(data['product_id'])
    if not product:
        return jsonify({'ok': False, 'msg': 'Product not found'}), 404
    stock = product['stock_qty'] if product['stock_qty'] is not None else 0
    if stock <= 0:
        return jsonify({'ok': False, 'msg': 'Out of stock'}), 400
    qty = data.get('qty', 1)
    sales_ctrl.add_to_cart(product, qty)
    return jsonify({'ok': True, 'cart': _cart_response()})


@app.route('/api/cart')
def cart_get():
    return jsonify(_cart_response())


@app.route('/api/cart/update', methods=['POST'])
def cart_update():
    data = request.json
    sales_ctrl.update_cart_qty(data['index'], data['qty'])
    return jsonify({'ok': True, 'cart': _cart_response()})


@app.route('/api/cart/remove', methods=['POST'])
def cart_remove():
    data = request.json
    sales_ctrl.remove_from_cart(data['index'])
    return jsonify({'ok': True, 'cart': _cart_response()})


@app.route('/api/cart/clear', methods=['POST'])
def cart_clear():
    sales_ctrl.clear_cart()
    return jsonify({'ok': True, 'cart': _cart_response()})


@app.route('/api/discount/apply', methods=['POST'])
def discount_apply():
    data = request.json
    code = data.get('code', '')
    ok, msg = sales_ctrl.apply_discount(code)
    return jsonify({'ok': ok, 'msg': msg, 'cart': _cart_response()})


@app.route('/api/sale/complete', methods=['POST'])
def sale_complete():
    data = request.json
    user = session.get('user')
    if not user:
        return jsonify({'ok': False, 'msg': 'Not authenticated'}), 401
    try:
        sale_id, receipt_path, receipt_text = sales_ctrl.finalize_sale(
            user['id'], data.get('payment_method', 'Cash')
        )
        return jsonify({'ok': True, 'sale_id': sale_id, 'receipt': receipt_text})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 400


@app.route('/api/inventory')
def get_inventory():
    items = inventory_ctrl.get_all_stock()
    result = []
    for i in items:
        if i['is_active']:
            result.append({
                'product_id': i['product_id'], 'name': i['product_name'],
                'stock': i['stock_qty'], 'min_level': i['min_stock_level'],
                'last_restocked': i['last_restocked'] or 'Never'
            })
    return jsonify(result)


@app.route('/api/inventory/low')
def get_low_stock():
    items = inventory_ctrl.get_low_stock()
    return jsonify([{
        'product_id': i['product_id'], 'name': i['product_name'],
        'stock': i['stock_qty'], 'min_level': i['min_stock_level']
    } for i in items])


@app.route('/api/inventory/restock', methods=['POST'])
def restock():
    data = request.json
    try:
        inventory_ctrl.restock_product(data['product_id'], data['qty'])
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 400


@app.route('/api/sales/history')
def sales_history():
    user = session.get('user')
    if not user or user.get('role') == 'attendant':
        return jsonify({'ok': False, 'msg': 'Admin only'}), 403
    period = request.args.get('period', 'today')
    start, end = report_ctrl.get_date_range(period)
    sales = report_ctrl.get_sales(start, end)
    result = []
    for s in sales:
        result.append({
            'id': s['id'], 'attendant': s['attendant'],
            'total': round(s['total'], 2), 'discount': round(s['discount_amount'], 2),
            'payment': s['payment_method'], 'time': s['created_at']
        })
    return jsonify(result)


@app.route('/api/sales/<int:sid>')
def sale_detail(sid):
    user = session.get('user')
    if not user or user.get('role') == 'attendant':
        return jsonify({'ok': False, 'msg': 'Admin only'}), 403
    data = sales_ctrl.sale_model.get_sale(sid)
    if not data:
        return jsonify({'ok': False, 'msg': 'Sale not found'}), 404
    return jsonify(data)


@app.route('/api/reports/summary')
def report_summary():
    period = request.args.get('period', 'today')
    start, end = report_ctrl.get_date_range(period)
    sales = report_ctrl.get_sales(start, end)
    total_rev = sum(s['total'] for s in sales)
    total_disc = sum(s['discount_amount'] for s in sales)
    low = inventory_ctrl.get_low_stock()
    return jsonify({
        'revenue': round(total_rev, 2),
        'transactions': len(sales),
        'discounts': round(total_disc, 2),
        'low_stock': len(low)
    })


@app.route('/api/reports/top')
def report_top():
    period = request.args.get('period', 'today')
    start, end = report_ctrl.get_date_range(period)
    top = report_ctrl.get_top_products(10, start, end)
    return jsonify([{
        'name': p['name'], 'qty': p['total_qty'],
        'revenue': round(p['total_revenue'], 2)
    } for p in top])


@app.route('/api/reports/chart')
def report_chart():
    data = report_ctrl.get_sales_chart_data(7)
    return jsonify([{
        'date': d['sale_date'], 'sales': d['num_sales'],
        'revenue': round(d['revenue'] or 0, 2)
    } for d in data])


@app.route('/api/users')
def get_users():
    users = user_model.get_all()
    return jsonify([{
        'id': u['id'], 'username': u['username'],
        'full_name': u['full_name'], 'role': u['role'],
        'active': bool(u['is_active']), 'created': u['created_at']
    } for u in users])


@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    try:
        user_model.create(data['username'], data['password'], data['full_name'], data.get('role', 'attendant'))
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 400


@app.route('/api/users/<int:uid>', methods=['PUT'])
def update_user(uid):
    data = request.json
    try:
        user_model.update(uid, full_name=data.get('full_name'), role=data.get('role'))
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 400


@app.route('/api/users/<int:uid>/password', methods=['POST'])
def change_password(uid):
    data = request.json
    try:
        user_model.change_password(uid, data['password'])
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 400


@app.route('/api/users/<int:uid>', methods=['DELETE'])
def delete_user(uid):
    user_model.delete(uid)
    return jsonify({'ok': True})


@app.route('/api/discounts')
def get_discounts():
    discs = discount_model.get_all()
    return jsonify([{
        'id': d['id'], 'code': d['code'], 'type': d['discount_type'],
        'value': d['value'], 'min_purchase': d['min_purchase'],
        'valid_until': d['valid_until'] or 'No expiry'
    } for d in discs])


@app.route('/api/discounts', methods=['POST'])
def create_discount():
    data = request.json
    try:
        discount_model.create(data['code'], data['type'], float(data['value']),
                              float(data.get('min_purchase', 0)), data.get('valid_until'))
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 400


@app.route('/api/discounts/<int:did>', methods=['DELETE'])
def delete_discount(did):
    discount_model.delete(did)
    return jsonify({'ok': True})


@app.route('/api/sync/sale', methods=['POST'])
def sync_sale():
    data = request.json
    try:
        sale_id = sales_ctrl.sale_model.create_sale(
            data['user_id'], data['items'],
            data.get('discount_amount', 0), data.get('payment_method', 'Cash')
        )
        return jsonify({'ok': True, 'sale_id': sale_id})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 400


def _cart_response():
    cart = sales_ctrl.get_cart()
    items = []
    for i, item in enumerate(cart):
        items.append({
            'index': i, 'product_id': item['product_id'],
            'name': item['name'], 'qty': item['qty'],
            'unit_price': item['unit_price'], 'subtotal': item['subtotal']
        })
    return {
        'items': items,
        'subtotal': round(sales_ctrl.get_cart_subtotal(), 2),
        'total': round(sales_ctrl.get_cart_total(), 2),
        'discount': sales_ctrl.applied_discount['message'] if sales_ctrl.applied_discount else ''
    }


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
