let currentUser = null;
let selectedProductId = null;
let selectedUserId = null;
let selectedDiscountId = null;
let currentPeriod = 'today';
let selectedCategoryId = null;
let cart = [];
let appliedDiscount = null;

let bsModal = null;
let bsReceiptModal = null;
let bsToast = null;

// ========== INDEXEDDB (Dexie) ==========
const db = new Dexie('WhispersLoungeDB');
db.version(2).stores({
    users: 'id, username, role',
    categories: 'id, name',
    products: 'id, name, category_id',
    inventory: 'product_id',
    sales: 'id, user_id, created_at',
    sale_items: 'id, sale_id, product_id',
    discounts: 'id, code',
    pending_sync: '++id, type, data'
}).upgrade(tx => {
    return tx.table('products').toCollection().modify(p => {
        if (p.unit === undefined) p.unit = '';
    });
});

async function syncFromServer() {
    if (!navigator.onLine) return;
    try {
        const [staff, cats, products, inventory, discounts] = await Promise.all([
            api('/api/staff'),
            api('/api/categories'),
            api('/api/products'),
            api('/api/inventory'),
            api('/api/discounts')
        ]);

        await db.transaction('rw', db.users, db.categories, db.products, db.inventory, db.discounts, async () => {
            await db.users.clear();
            for (const u of staff) await db.users.add({ id: u.id, username: u.username, full_name: u.full_name, role: u.role, is_active: 1 });

            await db.categories.clear();
            for (const c of cats) await db.categories.add({ id: c.id, name: c.name });

            await db.products.clear();
            for (const p of products) await db.products.add({
                id: p.id, name: p.name, category_id: p.category_id,
                price: p.price, cost: p.cost, unit: p.unit || '',
                barcode: p.barcode, stock_qty: p.stock
            });

            await db.inventory.clear();
            for (const i of inventory) await db.inventory.add({
                product_id: i.product_id, stock_qty: i.stock,
                min_stock_level: i.min_level, last_restocked: i.last_restocked
            });

            await db.discounts.clear();
            for (const d of discounts) await db.discounts.add({
                id: d.id, code: d.code, discount_type: d.type,
                value: d.value, min_purchase: d.min_purchase, valid_until: d.valid_until
            });
        });
        localStorage.setItem('whispers_synced', Date.now());
    } catch (e) {
        console.log('Sync failed, using cached data', e);
    }
}

async function syncPendingToServer() {
    if (!navigator.onLine) return;
    const pending = await db.pending_sync.toArray();
    for (const item of pending) {
        try {
            if (item.type === 'sale') {
                await api('/api/sync/sale', 'POST', item.data);
            } else if (item.type === 'product') {
                await api('/api/products', 'POST', item.data);
            } else if (item.type === 'product_edit') {
                await api('/api/products/' + item.data.id, 'PUT', item.data);
            } else if (item.type === 'inventory') {
                await api('/api/inventory/restock', 'POST', item.data);
            } else if (item.type === 'user') {
                await api('/api/users', 'POST', item.data);
            } else if (item.type === 'discount') {
                await api('/api/discounts', 'POST', item.data);
            }
            await db.pending_sync.delete(item.id);
        } catch (e) {}
    }
}

// ========== SCREEN MANAGEMENT ==========
function showScreen(name) {
    const adminScreens = ['dashboard', 'catalog', 'inventory', 'reports', 'analytics', 'discounts', 'users'];
    if (currentUser && currentUser.role === 'attendant' && adminScreens.includes(name)) return;

    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const screen = document.getElementById('screen-' + name);
    if (screen) screen.classList.add('active');

    if (name === 'staff-select') loadStaff();
    else if (name === 'pos') loadPOS();
    else if (name === 'dashboard') loadDashboard();
    else if (name === 'catalog') loadCatalog();
    else if (name === 'inventory') loadInventory();
    else if (name === 'reports') loadReports('today');
    else if (name === 'analytics') loadAnalytics();
    else if (name === 'sales-history') loadSalesHistory('today');
    else if (name === 'discounts') loadDiscounts();
    else if (name === 'users') loadUsers();
}

// ========== API HELPER (online only) ==========
async function api(url, method = 'GET', body = null) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(url, opts);
    return await res.json();
}

// ========== TOAST ==========
function showToast(msg, isError = false) {
    const el = document.getElementById('appToast');
    const body = document.getElementById('toast-body');
    body.textContent = msg;
    el.className = 'toast align-items-center text-white border-0' + (isError ? ' bg-danger' : ' bg-success');
    if (!bsToast) bsToast = new bootstrap.Toast(el, { delay: 2500 });
    bsToast.show();
}

// ========== MODAL ==========
function showModal(title, bodyHtml, footerHtml) {
    document.getElementById('modal-header').textContent = title;
    document.getElementById('modal-body').innerHTML = bodyHtml;
    document.getElementById('modal-footer').innerHTML = footerHtml;
    if (!bsModal) bsModal = new bootstrap.Modal(document.getElementById('appModal'));
    bsModal.show();
}
function closeModal() {
    if (bsModal) bsModal.hide();
}
function showReceiptModal(saleId, htmlContent) {
    document.getElementById('receipt-header').textContent = 'Receipt #' + saleId;
    document.getElementById('receipt-body').innerHTML = htmlContent;
    if (!bsReceiptModal) bsReceiptModal = new bootstrap.Modal(document.getElementById('receiptModal'));
    bsReceiptModal.show();
}

function buildReceiptHtml(receiptId, dateStr, attendant, payment, items, discountAmount, total) {
    let itemRows = '';
    items.forEach(item => {
        const unitText = item.unit ? ' (' + item.unit + ')' : '';
        itemRows += `<div class="receipt-row">
            <span>${item.name}${unitText}</span>
            <span>x${item.qty}</span>
            <span>$${item.subtotal.toFixed(2)}</span>
        </div>`;
        itemRows += `<div class="receipt-row receipt-sub">
            <span>@ $${item.unit_price.toFixed(2)} ea</span>
        </div>`;
    });

    let discountHtml = '';
    if (discountAmount > 0) {
        discountHtml = `<div class="receipt-row"><span>Discount</span><span class="text-danger">-$${discountAmount.toFixed(2)}</span></div>`;
    }

    return `<div class="thermal-receipt">
        <div class="receipt-header-block">
            <div class="receipt-business">WHISPERS LOUNGE</div>
            <div class="receipt-subtext">Premium Bar &amp; Nightclub</div>
        </div>
        <div class="receipt-divider"></div>
        <div class="receipt-meta">
            <div>Receipt #: ${receiptId}</div>
            <div>Date: ${dateStr}</div>
            <div>Attendant: ${attendant}</div>
            <div>Payment: ${payment}</div>
        </div>
        <div class="receipt-divider"></div>
        <div class="receipt-items">
            ${itemRows}
        </div>
        <div class="receipt-divider"></div>
        ${discountHtml}
        <div class="receipt-row receipt-total">
            <span>TOTAL</span>
            <span>$${total.toFixed(2)}</span>
        </div>
        <div class="receipt-divider"></div>
        <div class="receipt-footer">
            Thank you for your visit!
        </div>
    </div>`;
}

// ========== STAFF SELECT ==========
async function loadStaff() {
    let staff = await db.users.where('role').notEqual('admin').toArray();
    if (staff.length === 0) staff = await db.users.toArray();
    const grid = document.getElementById('staff-grid');
    grid.innerHTML = '';
    staff.forEach(u => {
        const col = document.createElement('div');
        col.className = 'flex-fill';
        col.innerHTML = `
            <form onsubmit="selectStaff(event, ${u.id})" class="w-100">
                <button type="submit" class="btn btn-staff w-100 py-4" style="border-color: #166534;">
                    <div class="fs-2 fw-bold" style="color: #166534;">${u.full_name}</div>
                    <div class="small text-secondary"><i class="bi bi-person-badge"></i> ${u.role.charAt(0).toUpperCase() + u.role.slice(1)}</div>
                </button>
            </form>`;
        grid.appendChild(col);
    });
}

async function selectStaff(e, id) {
    e.preventDefault();
    const user = await db.users.get(id);
    if (user) {
        currentUser = { id: user.id, name: user.full_name, role: user.role };
        showScreen('pos');
    }
}

// ========== ADMIN LOGIN ==========
function toggleAdminPass() {
    const input = document.getElementById('admin-password');
    const icon = document.getElementById('toggleIcon');
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.replace('bi-eye', 'bi-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.replace('bi-eye-slash', 'bi-eye');
    }
}

async function adminLogin() {
    const username = document.getElementById('admin-username').value.trim();
    const password = document.getElementById('admin-password').value.trim();
    if (!username || !password) {
        document.getElementById('admin-error').textContent = 'Please enter credentials';
        return;
    }
    let user = await db.users.where('username').equals(username).first();
    if (user && user.role === 'admin') {
        currentUser = { id: user.id, name: user.full_name, role: user.role };
        document.getElementById('admin-error').textContent = '';
        showScreen('dashboard');
    } else {
        const res = await api('/api/admin/login', 'POST', { username, password });
        if (res.ok) {
            currentUser = res.user;
            document.getElementById('admin-error').textContent = '';
            showScreen('dashboard');
        } else {
            document.getElementById('admin-error').textContent = res.msg;
        }
    }
}

async function doLogout() {
    currentUser = null;
    selectedCategoryId = null;
    cart = [];
    appliedDiscount = null;
    showScreen('staff-select');
}

// ========== POS ==========
async function loadPOS() {
    if (!currentUser) return showScreen('staff-select');
    document.getElementById('pos-user').textContent = '\u{1F464} ' + currentUser.name;
    setupNavButtons();
    await loadCategories();
    await filterProducts();
    renderCart();
}

function setupNavButtons() {
    const role = currentUser.role;
    const hamburger = document.getElementById('admin-hamburger');
    const salesBtn = document.getElementById('nav-sales-attendant');
    if (hamburger) hamburger.style.display = (role === 'attendant') ? 'none' : 'inline-flex';
    if (salesBtn) salesBtn.style.display = (role === 'attendant') ? 'inline-flex' : 'none';
}

async function loadCategories() {
    const cats = await db.categories.toArray();
    const bar = document.getElementById('category-bar');
    bar.innerHTML = '';
    const allBtn = document.createElement('button');
    allBtn.className = 'btn btn-sm cat-filter active';
    allBtn.textContent = 'All';
    allBtn.onclick = () => { selectedCategoryId = null; setActiveCategory(allBtn); filterProducts(); };
    bar.appendChild(allBtn);
    cats.forEach(c => {
        const btn = document.createElement('button');
        btn.className = 'btn btn-sm cat-filter';
        btn.textContent = c.name;
        btn.onclick = () => { selectedCategoryId = c.id; setActiveCategory(btn); filterProducts(); };
        bar.appendChild(btn);
    });
}

function setActiveCategory(el) {
    document.querySelectorAll('.cat-filter').forEach(b => b.classList.remove('active'));
    el.classList.add('active');
}

async function filterProducts() {
    const search = document.getElementById('search-input').value.toLowerCase();
    let products = await db.products.where('id').above(0).toArray();
    products = products.filter(p => {
        if (search) return p.name.toLowerCase().includes(search);
        if (selectedCategoryId) return p.category_id === selectedCategoryId;
        return true;
    });

    const grid = document.getElementById('product-grid');
    grid.innerHTML = '';
    products.forEach(p => {
        const stock = p.stock_qty || 0;
        const dotClass = stock <= 0 ? 'stock-zero' : stock <= 5 ? 'stock-low' : 'stock-ok';
        const btn = document.createElement('button');
        btn.className = 'btn btn-product';
        btn.style.cssText = 'flex: 0 0 calc(25% - 6px); max-width: calc(25% - 6px);';
        btn.innerHTML = `
            <span class="stock-dot ${dotClass}"></span>
            <div class="product-name">${p.name}</div>
            <div class="product-price" style="color: var(--accent);">$${p.price.toFixed(2)}</div>
            ${p.unit ? '<div class="product-unit text-muted">' + p.unit + '</div>' : ''}
            <div class="product-stock text-muted">Stock: ${stock}</div>`;
        btn.onclick = () => addToCart(p.id);
        grid.appendChild(btn);
    });
}

// ========== CART (in-memory + persisted) ==========
async function addToCart(productId) {
    const product = await db.products.get(productId);
    if (!product) return;
    const stock = product.stock_qty || 0;
    if (stock <= 0) return showToast('Out of stock!', true);

    const existing = cart.find(i => i.product_id === productId);
    if (existing) {
        if (existing.qty >= stock) return showToast('Not enough stock!', true);
        existing.qty++;
        existing.subtotal = existing.qty * existing.unit_price;
    } else {
        cart.push({
            product_id: productId,
            name: product.name,
            qty: 1,
            unit_price: product.price,
            subtotal: product.price,
            unit: product.unit || ''
        });
    }
    renderCart();
    updateCartBadge();
}

function renderCart() {
    const container = document.getElementById('cart-items');
    if (cart.length === 0) {
        container.innerHTML = '<p class="text-center text-muted mt-5 small">Cart is empty</p>';
    } else {
        container.innerHTML = '';
        cart.forEach((item, index) => {
            const div = document.createElement('div');
            div.className = 'cart-item bg-light mb-2 p-2 d-flex align-items-center';
            div.innerHTML = `
                <div class="flex-grow-1 min-width-0">
                    <div class="fw-bold small text-truncate">${item.name}</div>
                    <div class="small" style="color: var(--nav-bg); font-weight: 700;">$${item.subtotal.toFixed(2)}</div>
                </div>
                <div class="d-flex align-items-center gap-1">
                    <button class="btn btn-sm btn-outline-secondary" style="width:28px;height:28px;padding:0;" onclick="changeQty(${index}, -1)">-</button>
                    <span class="fw-bold small mx-1">${item.qty}</span>
                    <button class="btn btn-sm btn-outline-secondary" style="width:28px;height:28px;padding:0;" onclick="changeQty(${index}, 1)">+</button>
                    <button class="btn btn-sm text-danger" style="width:28px;height:28px;padding:0;font-size:0.7rem;" onclick="removeItem(${index})"><i class="bi bi-x-lg"></i></button>
                </div>`;
            container.appendChild(div);
        });
    }

    let subtotal = cart.reduce((sum, i) => sum + i.subtotal, 0);
    let total = subtotal;
    if (appliedDiscount) {
        if (appliedDiscount.type === 'percentage') {
            total = subtotal * (1 - appliedDiscount.value / 100);
        } else {
            total = subtotal - appliedDiscount.value;
        }
        if (total < 0) total = 0;
    }
    document.getElementById('cart-subtotal').textContent = subtotal.toFixed(2);
    document.getElementById('cart-total').textContent = total.toFixed(2);
    document.getElementById('discount-msg').textContent = appliedDiscount ? appliedDiscount.message : '';
    updateCartBadge();
}

function changeQty(index, delta) {
    const item = cart[index];
    if (!item) return;
    item.qty += delta;
    if (item.qty <= 0) {
        cart.splice(index, 1);
    } else {
        item.subtotal = item.qty * item.unit_price;
    }
    renderCart();
}

function removeItem(index) {
    cart.splice(index, 1);
    renderCart();
}

async function applyDiscount() {
    const code = document.getElementById('discount-input').value.trim().toUpperCase();
    if (!code) return;
    const disc = await db.discounts.where('code').equals(code).first();
    if (disc) {
        appliedDiscount = { type: disc.discount_type, value: disc.value, message: disc.discount_type === 'percentage' ? disc.value + '% off' : '$' + disc.value.toFixed(2) + ' off' };
    } else {
        appliedDiscount = null;
        document.getElementById('discount-msg').textContent = 'Invalid code';
        document.getElementById('discount-msg').style.color = '#dc3545';
    }
    renderCart();
}

async function completeSale() {
    if (cart.length === 0) return showToast('Add items to cart first!', true);
    const payment = document.querySelector('input[name="payment"]:checked').value;

    let subtotal = cart.reduce((sum, i) => sum + i.subtotal, 0);
    let discountAmount = 0;
    if (appliedDiscount) {
        if (appliedDiscount.type === 'percentage') discountAmount = subtotal * (appliedDiscount.value / 100);
        else discountAmount = appliedDiscount.value;
    }
    let total = Math.max(0, subtotal - discountAmount);

    if (!confirm('Complete sale for $' + total.toFixed(2) + ' (' + payment + ')?')) return;

    const now = new Date().toISOString().replace('T', ' ').slice(0, 19);
    const saleId = Date.now();

    await db.sales.add({
        id: saleId,
        user_id: currentUser.id,
        total: total,
        discount_amount: discountAmount,
        payment_method: payment,
        created_at: now
    });

    for (const item of cart) {
        await db.sale_items.add({
            id: Date.now() + Math.random(),
            sale_id: saleId,
            product_id: item.product_id,
            qty: item.qty,
            unit_price: item.unit_price,
            subtotal: item.subtotal
        });

        const product = await db.products.get(item.product_id);
        if (product) {
            await db.products.update(item.product_id, { stock_qty: (product.stock_qty || 0) - item.qty });
        }
        await db.inventory.where('product_id').equals(item.product_id).modify(i => {
            i.stock_qty = Math.max(0, i.stock_qty - item.qty);
        });
    }

    await db.pending_sync.add({ type: 'sale', data: { sale_id: saleId, user_id: currentUser.id, total, discount_amount: discountAmount, payment_method: payment, items: cart } });

    const user = await db.users.get(currentUser.id);
    const saleIdShort = String(saleId).slice(-6);
    const receiptHtml = buildReceiptHtml(saleIdShort, now, user ? user.full_name : 'Unknown', payment, cart, discountAmount, total);

    showToast('Sale #' + saleIdShort + ' completed!');
    cart = [];
    appliedDiscount = null;
    document.getElementById('discount-input').value = '';
    document.getElementById('discount-msg').textContent = '';
    renderCart();
    filterProducts();
    showReceiptModal(saleIdShort, receiptHtml);
}

// ========== DASHBOARD ==========
async function loadDashboard() {
    const today = new Date().toISOString().slice(0, 10);
    const sales = await db.sales.where('created_at').aboveOrEqual(today).toArray();
    const totalRev = sales.reduce((sum, s) => sum + s.total, 0);
    const totalDisc = sales.reduce((sum, s) => sum + s.discount_amount, 0);

    const products = await db.products.toArray();
    const lowStock = products.filter(p => (p.stock_qty || 0) <= 5).length;

    document.getElementById('stat-revenue').textContent = '$' + totalRev.toFixed(2);
    document.getElementById('stat-tx').textContent = sales.length;
    document.getElementById('stat-disc').textContent = '$' + totalDisc.toFixed(2);
    document.getElementById('stat-low').textContent = lowStock;

    const recentSales = await db.sales.orderBy('id').reverse().limit(10).toArray();
    const container = document.getElementById('dashboard-recent-sales');
    if (recentSales.length === 0) {
        container.innerHTML = '<p class="text-center text-muted">No sales yet.</p>';
        return;
    }
    let html = '';
    for (const s of recentSales) {
        const user = await db.users.get(s.user_id);
        const time = s.created_at ? s.created_at.split(' ')[1] || s.created_at : '-';
        const shortId = String(s.id).slice(-6);
        html += `<div class="d-flex align-items-center justify-content-between bg-white border rounded-3 p-2 mb-2" style="cursor:pointer;" onclick="viewSaleDetail(${s.id})">
            <span class="fw-bold" style="color: var(--nav-bg);">${user ? user.full_name : '?'}</span>
            <span class="badge bg-light text-dark">${s.payment_method}</span>
            <span class="fw-bold" style="color: var(--accent);">$${s.total.toFixed(2)}</span>
            <span class="text-muted small">#${shortId}</span>
        </div>`;
    }
    container.innerHTML = html;
}

// ========== CATALOG ==========
async function loadCatalog() {
    const search = document.getElementById('catalog-search')?.value?.toLowerCase() || '';
    let products = await db.products.toArray();
    if (search) products = products.filter(p => p.name.toLowerCase().includes(search));

    const cats = await db.categories.toArray();
    const catMap = {};
    cats.forEach(c => catMap[c.id] = c.name);

    const container = document.getElementById('catalog-table');
    let html = '<table class="table table-hover"><thead class="table-light"><tr><th>ID</th><th>Name</th><th>Category</th><th>Unit</th><th>Price</th><th>Cost</th><th>Margin</th><th>Stock</th><th>Barcode</th><th></th></tr></thead><tbody>';
    products.forEach(p => {
        const margin = p.price > 0 ? Math.round(((p.price - (p.cost || 0)) / p.price) * 100) : 0;
        html += `<tr onclick="selectCatalogItem(${p.id}, this)" data-id="${p.id}" style="cursor:pointer;">
            <td>${p.id}</td><td>${p.name}</td><td>${catMap[p.category_id] || '-'}</td>
            <td>${p.unit || '-'}</td>
            <td class="fw-bold" style="color:var(--accent);">$${p.price.toFixed(2)}</td><td>$${(p.cost || 0).toFixed(2)}</td>
            <td class="fw-bold">${margin}%</td>
            <td>${p.stock_qty || 0}</td><td>${p.barcode || '-'}</td>
            <td><button class="btn btn-sm btn-warning" onclick="event.stopPropagation(); editProductModal(${p.id})"><i class="bi bi-pencil"></i></button></td></tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
}

function selectCatalogItem(id, el) {
    selectedProductId = id;
    document.querySelectorAll('#catalog-table tr').forEach(r => r.classList.remove('table-success'));
    el.classList.add('table-success');
}

async function deleteSelectedProduct() {
    if (!selectedProductId) return showToast('Select a product first', true);
    if (!confirm('Delete this product?')) return;
    await db.products.delete(selectedProductId);
    await db.inventory.where('product_id').equals(selectedProductId).delete();
    selectedProductId = null;
    loadCatalog();
    showToast('Product deleted');
}

async function showProductModal() {
    const cats = await db.categories.toArray();
    let catOpts = '<option value="">None</option>';
    cats.forEach(c => catOpts += '<option value="' + c.id + '">' + c.name + '</option>');
    const body = `
        <div class="mb-3"><label class="form-label">Name</label><input id="m-prod-name" class="form-control"></div>
        <div class="mb-3"><label class="form-label">Category</label><select id="m-prod-cat" class="form-select">${catOpts}</select></div>
        <div class="row mb-3">
            <div class="col"><label class="form-label">Selling Price ($)</label><input id="m-prod-price" type="number" step="0.01" class="form-control"></div>
            <div class="col"><label class="form-label">Cost ($)</label><input id="m-prod-cost" type="number" step="0.01" value="0" class="form-control"></div>
        </div>
        <div class="mb-3"><label class="form-label">Unit</label><input id="m-prod-unit" class="form-control" placeholder="e.g. Bottle, Can, Shot, Jug, Pack"></div>
        <div class="mb-3"><label class="form-label">Barcode</label><input id="m-prod-barcode" class="form-control"></div>`;
    const footer = `<button type="button" class="btn btn-outline-secondary" onclick="closeModal()">Cancel</button>
        <button type="button" class="btn fw-bold text-light" style="background:#166534;border-color:#166534;" onclick="saveProduct()">Save</button>`;
    showModal('Add Product', body, footer);
}

async function saveProduct() {
    const name = document.getElementById('m-prod-name').value.trim();
    const catId = document.getElementById('m-prod-cat').value || null;
    const price = parseFloat(document.getElementById('m-prod-price').value);
    const cost = parseFloat(document.getElementById('m-prod-cost').value) || 0;
    const unit = document.getElementById('m-prod-unit').value.trim();
    const barcode = document.getElementById('m-prod-barcode').value.trim() || null;
    if (!name || !price) return showToast('Name and price required', true);

    const id = Date.now();
    await db.products.add({ id, name, category_id: catId ? parseInt(catId) : null, price, cost, unit, barcode, stock_qty: 0 });
    await db.inventory.add({ product_id: id, stock_qty: 0, min_stock_level: 5, last_restocked: null });
    await db.pending_sync.add({ type: 'product', data: { name, category_id: catId, price, cost, unit, barcode } });
    closeModal();
    loadCatalog();
    showToast('Product added');
}

async function editProductModal(productId) {
    const product = await db.products.get(productId);
    if (!product) return showToast('Product not found', true);
    const inv = await db.inventory.where('product_id').equals(productId).first();
    const cats = await db.categories.toArray();
    let catOpts = '<option value="">None</option>';
    cats.forEach(c => {
        const sel = product.category_id === c.id ? ' selected' : '';
        catOpts += '<option value="' + c.id + '"' + sel + '>' + c.name + '</option>';
    });
    const stockQty = inv ? inv.stock_qty : 0;
    const minLevel = inv ? inv.min_stock_level : 5;
    const body = `
        <div class="mb-3"><label class="form-label">Product Name</label><input id="m-edit-name" class="form-control" value="${product.name}"></div>
        <div class="mb-3"><label class="form-label">Category</label><select id="m-edit-cat" class="form-select">${catOpts}</select></div>
        <div class="row mb-3">
            <div class="col"><label class="form-label">Selling Price ($)</label><input id="m-edit-price" type="number" step="0.01" class="form-control" value="${product.price}"></div>
            <div class="col"><label class="form-label">Cost ($)</label><input id="m-edit-cost" type="number" step="0.01" class="form-control" value="${product.cost || 0}"></div>
        </div>
        <div class="mb-3"><label class="form-label">Unit</label><input id="m-edit-unit" class="form-control" value="${product.unit || ''}" placeholder="e.g. Bottle, Can, Shot, Jug, Pack"></div>
        <div class="row mb-3">
            <div class="col"><label class="form-label">Stock Qty</label><input id="m-edit-stock" type="number" class="form-control" value="${stockQty}"></div>
            <div class="col"><label class="form-label">Min Stock Level</label><input id="m-edit-minstock" type="number" class="form-control" value="${minLevel}"></div>
        </div>
        <div class="mb-3"><label class="form-label">Barcode</label><input id="m-edit-barcode" class="form-control" value="${product.barcode || ''}"></div>
        <div class="text-muted small">Margin: <strong id="m-edit-margin">${product.price > 0 ? Math.round(((product.price - (product.cost || 0)) / product.price) * 100) : 0}%</strong></div>`;
    const footer = `<button type="button" class="btn btn-outline-secondary" onclick="closeModal()">Cancel</button>
        <button type="button" class="btn fw-bold text-light" style="background:#166534;border-color:#166534;" onclick="saveProductEdit(${productId})">Update</button>`;
    showModal('Edit Product', body, footer);
    document.getElementById('m-edit-price').addEventListener('input', updateEditMargin);
    document.getElementById('m-edit-cost').addEventListener('input', updateEditMargin);
}

function updateEditMargin() {
    const price = parseFloat(document.getElementById('m-edit-price').value) || 0;
    const cost = parseFloat(document.getElementById('m-edit-cost').value) || 0;
    const margin = price > 0 ? Math.round(((price - cost) / price) * 100) : 0;
    document.getElementById('m-edit-margin').textContent = margin + '%';
}

async function saveProductEdit(productId) {
    const name = document.getElementById('m-edit-name').value.trim();
    const catId = document.getElementById('m-edit-cat').value || null;
    const price = parseFloat(document.getElementById('m-edit-price').value);
    const cost = parseFloat(document.getElementById('m-edit-cost').value) || 0;
    const unit = document.getElementById('m-edit-unit').value.trim();
    const stockQty = parseInt(document.getElementById('m-edit-stock').value) || 0;
    const minLevel = parseInt(document.getElementById('m-edit-minstock').value) || 5;
    const barcode = document.getElementById('m-edit-barcode').value.trim() || null;
    if (!name || !price) return showToast('Name and price required', true);

    await db.products.update(productId, { name, category_id: catId ? parseInt(catId) : null, price, cost, unit, barcode, stock_qty: stockQty });
    await db.inventory.where('product_id').equals(productId).modify(i => {
        i.stock_qty = stockQty;
        i.min_stock_level = minLevel;
    });
    await db.pending_sync.add({ type: 'product_edit', data: { id: productId, name, category_id: catId ? parseInt(catId) : null, price, cost, unit, barcode, stock_qty: stockQty } });
    closeModal();
    loadCatalog();
    showToast('Product updated');
}

// ========== INVENTORY ==========
async function loadInventory() {
    const items = await db.inventory.toArray();
    const products = await db.products.toArray();
    const prodMap = {};
    products.forEach(p => prodMap[p.id] = p);

    const container = document.getElementById('inventory-table');
    let html = '<table class="table table-hover"><thead class="table-light"><tr><th>Product</th><th>Stock</th><th>Min Level</th><th>Last Restocked</th></tr></thead><tbody>';
    items.forEach(i => {
        const prod = prodMap[i.product_id];
        if (!prod || !prod.name) return;
        const cls = i.stock_qty <= i.min_stock_level ? 'text-danger' : '';
        html += `<tr onclick="selectInventoryItem(${i.product_id}, this)" data-id="${i.product_id}" style="cursor:pointer;">
            <td>${prod.name}</td><td class="${cls} fw-bold">${i.stock_qty}</td>
            <td>${i.min_stock_level}</td><td>${i.last_restocked || 'Never'}</td></tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
}

function selectInventoryItem(id, el) {
    selectedProductId = id;
    document.querySelectorAll('#inventory-table tr').forEach(r => r.classList.remove('table-success'));
    el.classList.add('table-success');
}

async function loadLowStock() {
    const items = await db.inventory.toArray();
    const products = await db.products.toArray();
    const prodMap = {};
    products.forEach(p => prodMap[p.id] = p);

    const container = document.getElementById('inventory-table');
    let html = '<table class="table table-hover"><thead class="table-light"><tr><th>Product</th><th>Stock</th><th>Min Level</th></tr></thead><tbody>';
    items.forEach(i => {
        if (i.stock_qty > i.min_stock_level) return;
        const prod = prodMap[i.product_id];
        if (!prod || !prod.name) return;
        html += `<tr onclick="selectInventoryItem(${i.product_id}, this)" data-id="${i.product_id}" style="cursor:pointer;">
            <td>${prod.name}</td><td class="text-danger fw-bold">${i.stock_qty}</td><td>${i.min_stock_level}</td></tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
}

async function restockFirst() {
    if (!selectedProductId) return showToast('Select a product first', true);
    const body = `<div class="mb-3"><label class="form-label">Quantity to add</label><input id="m-restock-qty" type="number" value="10" class="form-control"></div>`;
    const footer = `<button type="button" class="btn btn-outline-secondary" onclick="closeModal()">Cancel</button>
        <button type="button" class="btn fw-bold text-light" style="background:#166534;border-color:#166534;" onclick="doRestock()">Restock</button>`;
    showModal('Restock Product', body, footer);
}

async function doRestock() {
    const qty = parseInt(document.getElementById('m-restock-qty').value);
    if (!qty || qty <= 0) return showToast('Enter valid quantity', true);

    await db.inventory.where('product_id').equals(selectedProductId).modify(i => {
        i.stock_qty += qty;
        i.last_restocked = new Date().toISOString().slice(0, 19);
    });
    const product = await db.products.get(selectedProductId);
    if (product) {
        await db.products.update(selectedProductId, { stock_qty: (product.stock_qty || 0) + qty });
    }
    await db.pending_sync.add({ type: 'inventory', data: { product_id: selectedProductId, qty } });
    closeModal();
    loadInventory();
    showToast('Restocked!');
}

// ========== REPORTS ==========
async function loadReports(period, btn) {
    currentPeriod = period || 'today';
    if (btn) {
        btn.closest('.d-flex').querySelectorAll('.cat-filter').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    }

    const now = new Date();
    let startDate;
    if (currentPeriod === 'today') startDate = now.toISOString().slice(0, 10);
    else if (currentPeriod === 'yesterday') {
        const y = new Date(now); y.setDate(y.getDate() - 1);
        startDate = y.toISOString().slice(0, 10);
    }
    else if (currentPeriod === 'week') {
        const w = new Date(now); w.setDate(w.getDate() - 7);
        startDate = w.toISOString().slice(0, 10);
    }
    else if (currentPeriod === 'month') {
        const m = new Date(now); m.setDate(m.getDate() - 30);
        startDate = m.toISOString().slice(0, 10);
    }

    const allSales = await db.sales.toArray();
    const filtered = allSales.filter(s => s.created_at >= startDate);
    const totalRev = filtered.reduce((sum, s) => sum + s.total, 0);
    const totalDisc = filtered.reduce((sum, s) => sum + s.discount_amount, 0);

    document.getElementById('rpt-revenue').textContent = '$' + totalRev.toFixed(2);
    document.getElementById('rpt-sales').textContent = filtered.length;
    document.getElementById('rpt-disc').textContent = '$' + totalDisc.toFixed(2);

    const topProducts = {};
    const saleItems = await db.sale_items.toArray();
    saleItems.forEach(si => {
        const sale = filtered.find(s => s.id === si.sale_id);
        if (sale) {
            if (!topProducts[si.product_id]) topProducts[si.product_id] = { qty: 0, revenue: 0 };
            topProducts[si.product_id].qty += si.qty;
            topProducts[si.product_id].revenue += si.subtotal;
        }
    });

    const products = await db.products.toArray();
    const prodMap = {};
    products.forEach(p => prodMap[p.id] = p.name);

    const topContainer = document.getElementById('top-products');
    const sorted = Object.entries(topProducts).sort((a, b) => b[1].revenue - a[1].revenue).slice(0, 10);
    topContainer.innerHTML = '';
    if (sorted.length === 0) {
        topContainer.innerHTML = '<p class="text-muted small">No data</p>';
    }
    sorted.forEach(([pid, data]) => {
        topContainer.innerHTML += '<div class="d-flex justify-content-between py-2 border-bottom small"><span>' + (prodMap[pid] || 'Unknown') + '</span><span class="fw-bold" style="color:var(--nav-bg);">$' + data.revenue.toFixed(2) + '</span></div>';
    });

    const chartData = {};
    filtered.forEach(s => {
        const date = s.created_at.slice(0, 10);
        if (!chartData[date]) chartData[date] = 0;
        chartData[date] += s.total;
    });
    const chartArr = Object.entries(chartData).sort().map(([date, revenue]) => ({ date, revenue }));
    drawChart(chartArr);
}

function drawChart(data) {
    const canvas = document.getElementById('chart-canvas');
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    canvas.width = canvas.offsetWidth * dpr;
    canvas.height = 200 * dpr;
    ctx.scale(dpr, dpr);
    const w = canvas.offsetWidth, h = 200;
    ctx.clearRect(0, 0, w, h);

    if (!data || data.length === 0) {
        ctx.fillStyle = '#888';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('No data available', w / 2, h / 2);
        return;
    }

    const maxRev = Math.max(...data.map(d => d.revenue), 1);
    const margin = 40;
    const barW = Math.max(20, (w - margin * 2) / data.length - 10);
    const chartH = h - margin * 2;

    data.forEach((d, i) => {
        const x = margin + i * (barW + 10);
        const barH = (d.revenue / maxRev) * chartH;
        const y1 = h - margin;
        const y2 = y1 - barH;
        ctx.fillStyle = '#166534';
        ctx.fillRect(x, y2, barW, barH);
        ctx.strokeStyle = '#e2a526';
        ctx.lineWidth = 1;
        ctx.strokeRect(x, y2, barW, barH);
        ctx.fillStyle = '#888';
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(d.date.slice(5), x + barW / 2, y1 + 15);
        ctx.fillStyle = '#166534';
        ctx.font = 'bold 10px sans-serif';
        ctx.fillText('$' + d.revenue.toFixed(0), x + barW / 2, y2 - 6);
    });
}

// ========== SALES HISTORY ==========
let shPeriod = 'today';

async function loadSalesHistory(period, btn) {
    shPeriod = period || 'today';
    if (btn) {
        btn.closest('.d-flex').querySelectorAll('.cat-filter').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    }

    const now = new Date();
    let startDate;
    if (shPeriod === 'today') startDate = now.toISOString().slice(0, 10);
    else if (shPeriod === 'yesterday') {
        const y = new Date(now); y.setDate(y.getDate() - 1);
        startDate = y.toISOString().slice(0, 10);
    }
    else if (shPeriod === 'week') {
        const w = new Date(now); w.setDate(w.getDate() - 7);
        startDate = w.toISOString().slice(0, 10);
    }
    else if (shPeriod === 'month') {
        const m = new Date(now); m.setDate(m.getDate() - 30);
        startDate = m.toISOString().slice(0, 10);
    }

    const allSales = await db.sales.orderBy('id').reverse().toArray();
    const filtered = allSales.filter(s => s.created_at >= startDate);
    let totalRev = 0, totalDisc = 0;
    filtered.forEach(s => { totalRev += s.total; totalDisc += s.discount_amount; });

    document.getElementById('sh-revenue').textContent = '$' + totalRev.toFixed(2);
    document.getElementById('sh-tx').textContent = filtered.length;
    document.getElementById('sh-disc').textContent = '$' + totalDisc.toFixed(2);

    const products = await db.products.toArray();
    const container = document.getElementById('sales-history-table');
    if (filtered.length === 0) {
        container.innerHTML = '<p class="text-center text-muted mt-4">No sales for this period.</p>';
        return;
    }

    let html = '<table class="table table-hover"><thead class="table-light"><tr><th>#</th><th>Attendant</th><th>Total</th><th>Discount</th><th>Payment</th><th>Time</th><th></th></tr></thead><tbody>';
    for (const s of filtered) {
        const user = await db.users.get(s.user_id);
        const time = s.created_at ? s.created_at.split(' ')[1] || s.created_at : '-';
        const shortId = String(s.id).slice(-6);
        html += '<tr style="cursor:pointer;">' +
            '<td class="fw-bold">#' + shortId + '</td>' +
            '<td>' + (user ? user.full_name : '?') + '</td>' +
            '<td class="fw-bold" style="color:var(--accent);">$' + s.total.toFixed(2) + '</td>' +
            '<td>' + (s.discount_amount > 0 ? '-$' + s.discount_amount.toFixed(2) : '-') + '</td>' +
            '<td><span class="badge bg-light text-dark">' + s.payment_method + '</span></td>' +
            '<td class="text-muted small">' + time + '</td>' +
            '<td><button class="btn btn-sm btn-success" onclick="viewSaleDetail(' + s.id + ')">View</button></td>' +
            '</tr>';
    }
    html += '</tbody></table>';
    container.innerHTML = html;
}

async function viewSaleDetail(saleId) {
    const sale = await db.sales.get(saleId);
    if (!sale) return showToast('Sale not found', true);
    const user = await db.users.get(sale.user_id);
    const items = await db.sale_items.where('sale_id').equals(saleId).toArray();
    const products = await db.products.toArray();
    const prodMap = {};
    products.forEach(p => prodMap[p.id] = p);

    const receiptItems = items.map(item => {
        const prod = prodMap[item.product_id];
        return {
            name: prod ? prod.name : 'Unknown',
            unit: prod ? prod.unit || '' : '',
            qty: item.qty,
            unit_price: item.unit_price,
            subtotal: item.subtotal
        };
    });

    const saleIdShort = String(saleId).slice(-6);
    const receiptHtml = buildReceiptHtml(saleIdShort, sale.created_at, user ? user.full_name : 'Unknown', sale.payment_method, receiptItems, sale.discount_amount, sale.total);
    const footer = '<button type="button" class="btn fw-bold text-light w-100" style="background:#166534;border-color:#166534;" onclick="closeModal()">Close</button>';
    showModal('Sale #' + saleIdShort, receiptHtml, footer);
}

// ========== DISCOUNTS ==========
async function loadDiscounts() {
    const discs = await db.discounts.toArray();
    const container = document.getElementById('discounts-table');
    let html = '<table class="table table-hover"><thead class="table-light"><tr><th>Code</th><th>Type</th><th>Value</th><th>Min Purchase</th><th>Valid Until</th></tr></thead><tbody>';
    discs.forEach(d => {
        const val = d.discount_type === 'percentage' ? d.value + '%' : '$' + d.value.toFixed(2);
        html += '<tr onclick="selectDiscountItem(' + d.id + ', this)" data-id="' + d.id + '" style="cursor:pointer;">' +
            '<td class="fw-bold">' + d.code + '</td><td>' + d.discount_type + '</td>' +
            '<td class="fw-bold" style="color:var(--nav-bg);">' + val + '</td><td>$' + (d.min_purchase || 0).toFixed(2) + '</td><td>' + (d.valid_until || 'No expiry') + '</td></tr>';
    });
    html += '</tbody></table>';
    container.innerHTML = html;
}

function selectDiscountItem(id, el) {
    selectedDiscountId = id;
    document.querySelectorAll('#discounts-table tr').forEach(r => r.classList.remove('table-success'));
    el.classList.add('table-success');
}

async function deleteSelectedDiscount() {
    if (!selectedDiscountId) return showToast('Select a discount first', true);
    if (!confirm('Delete this discount?')) return;
    await db.discounts.delete(selectedDiscountId);
    selectedDiscountId = null;
    loadDiscounts();
    showToast('Discount deleted');
}

function showDiscountModal() {
    const body = `
        <div class="mb-3"><label class="form-label">Code</label><input id="m-disc-code" class="form-control" placeholder="e.g. HAPPY20"></div>
        <div class="mb-3"><label class="form-label">Type</label>
            <select id="m-disc-type" class="form-select"><option value="percentage">Percentage</option><option value="fixed">Fixed ($)</option></select></div>
        <div class="mb-3"><label class="form-label">Value</label><input id="m-disc-value" type="number" step="0.01" class="form-control"></div>
        <div class="mb-3"><label class="form-label">Min Purchase ($)</label><input id="m-disc-min" type="number" step="0.01" value="0" class="form-control"></div>
        <div class="mb-3"><label class="form-label">Valid Until (YYYY-MM-DD)</label><input id="m-disc-until" type="date" class="form-control"></div>`;
    const footer = `<button type="button" class="btn btn-outline-secondary" onclick="closeModal()">Cancel</button>
        <button type="button" class="btn fw-bold text-light" style="background:#166534;border-color:#166534;" onclick="saveDiscount()">Create</button>`;
    showModal('Add Discount', body, footer);
}

async function saveDiscount() {
    const code = document.getElementById('m-disc-code').value.trim().toUpperCase();
    const dtype = document.getElementById('m-disc-type').value;
    const value = parseFloat(document.getElementById('m-disc-value').value);
    const minP = parseFloat(document.getElementById('m-disc-min').value) || 0;
    const until = document.getElementById('m-disc-until').value || null;
    if (!code || !value) return showToast('Code and value required', true);

    await db.discounts.add({ code, discount_type: dtype, value, min_purchase: minP, valid_until: until });
    await db.pending_sync.add({ type: 'discount', data: { code, type: dtype, value, min_purchase: minP, valid_until: until } });
    closeModal();
    loadDiscounts();
    showToast('Discount created');
}

// ========== USERS ==========
async function loadUsers() {
    const users = await db.users.toArray();
    const container = document.getElementById('users-table');
    let html = '<table class="table table-hover"><thead class="table-light"><tr><th>Name</th><th>Username</th><th>Role</th><th>Status</th></tr></thead><tbody>';
    users.forEach(u => {
        const statusClass = u.is_active ? 'text-success' : 'text-danger';
        const statusText = u.is_active ? 'Active' : 'Inactive';
        html += '<tr onclick="selectUserItem(' + u.id + ', this)" data-id="' + u.id + '" style="cursor:pointer;">' +
            '<td>' + u.full_name + '</td><td>' + u.username + '</td>' +
            '<td class="fw-bold" style="color:var(--nav-bg);">' + u.role.charAt(0).toUpperCase() + u.role.slice(1) + '</td>' +
            '<td class="' + statusClass + '">' + statusText + '</td></tr>';
    });
    html += '</tbody></table>';
    container.innerHTML = html;
}

function selectUserItem(id, el) {
    selectedUserId = id;
    document.querySelectorAll('#users-table tr').forEach(r => r.classList.remove('table-success'));
    el.classList.add('table-success');
}

async function deleteSelectedUser() {
    if (!selectedUserId) return showToast('Select a user first', true);
    if (!confirm('Deactivate this user?')) return;
    await db.users.update(selectedUserId, { is_active: 0 });
    selectedUserId = null;
    loadUsers();
    showToast('User deactivated');
}

function showUserModal() {
    const body = `
        <div class="mb-3"><label class="form-label">Username</label><input id="m-user-user" class="form-control"></div>
        <div class="mb-3"><label class="form-label">Full Name</label><input id="m-user-name" class="form-control"></div>
        <div class="mb-3"><label class="form-label">Password</label><input id="m-user-pass" type="password" class="form-control"></div>
        <div class="mb-3"><label class="form-label">Role</label>
            <select id="m-user-role" class="form-select">
                <option value="attendant">Attendant</option><option value="manager">Manager</option><option value="admin">Admin</option>
            </select></div>`;
    const footer = `<button type="button" class="btn btn-outline-secondary" onclick="closeModal()">Cancel</button>
        <button type="button" class="btn fw-bold text-light" style="background:#166534;border-color:#166534;" onclick="saveUser()">Create</button>`;
    showModal('Add User', body, footer);
}

async function saveUser() {
    const username = document.getElementById('m-user-user').value.trim();
    const fullName = document.getElementById('m-user-name').value.trim();
    const password = document.getElementById('m-user-pass').value;
    const role = document.getElementById('m-user-role').value;
    if (!username || !fullName || !password) return showToast('All fields required', true);

    const id = Date.now();
    await db.users.add({ id, username, full_name: fullName, password, role, is_active: 1 });
    await db.pending_sync.add({ type: 'user', data: { username, password, full_name: fullName, role } });
    closeModal();
    loadUsers();
    showToast('User created');
}

function showPasswordModal() {
    if (!selectedUserId) return showToast('Select a user first', true);
    const body = '<div class="mb-3"><label class="form-label">New Password</label><input id="m-new-pass" type="password" class="form-control"></div>';
    const footer = `<button type="button" class="btn btn-outline-secondary" onclick="closeModal()">Cancel</button>
        <button type="button" class="btn fw-bold text-light" style="background:#166534;border-color:#166534;" onclick="savePassword()">Update</button>`;
    showModal('Change Password', body, footer);
}

async function savePassword() {
    const pwd = document.getElementById('m-new-pass').value;
    if (!pwd) return showToast('Enter new password', true);
    await db.users.update(selectedUserId, { password: pwd });
    closeModal();
    showToast('Password updated');
}

// ========== INSTALL APP ==========
let deferredPrompt = null;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    document.getElementById('installBtn').style.display = 'inline-flex';
});

window.addEventListener('appinstalled', () => {
    deferredPrompt = null;
    document.getElementById('installBtn').style.display = 'none';
    showToast('App installed!');
});

async function installApp() {
    if (!deferredPrompt) {
        showToast('Open in Chrome/Edge browser to install', true);
        return;
    }
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    deferredPrompt = null;
    document.getElementById('installBtn').style.display = 'none';
}

async function shareApp() {
    const shareData = {
        title: 'Whispers Lounge POS',
        text: 'Whispers Lounge POS System - Open to start',
        url: window.location.href
    };
    if (navigator.share) {
        try {
            await navigator.share(shareData);
        } catch (e) {}
    } else {
        try {
            await navigator.clipboard.writeText(window.location.href);
            showToast('Link copied to clipboard!');
        } catch (e) {
            prompt('Copy this link:', window.location.href);
        }
    }
}

// ========== MOBILE CART ==========
let mobileCartOpen = false;

function toggleMobileCart() {
    mobileCartOpen = !mobileCartOpen;
    const panel = document.getElementById('mobileCartPanel');
    const badge = document.getElementById('cartBadge');
    if (mobileCartOpen) {
        panel.classList.add('show');
        renderCartMobile();
    } else {
        panel.classList.remove('show');
    }
    updateCartBadge();
}

function updateCartBadge() {
    const badge = document.getElementById('cartBadge');
    const count = cart.reduce((sum, i) => sum + i.qty, 0);
    if (count > 0) {
        badge.textContent = count;
        badge.style.display = 'flex';
    } else {
        badge.style.display = 'none';
    }
}

function renderCartMobile() {
    const container = document.getElementById('cart-items-mobile');
    if (cart.length === 0) {
        container.innerHTML = '<p class="text-center text-muted mt-5 small">Cart is empty</p>';
    } else {
        container.innerHTML = '';
        cart.forEach((item, index) => {
            const div = document.createElement('div');
            div.className = 'cart-item bg-light mb-2 p-2 d-flex align-items-center';
            div.innerHTML = `
                <div class="flex-grow-1 min-width-0">
                    <div class="fw-bold small text-truncate">${item.name}</div>
                    <div class="small" style="color: var(--nav-bg); font-weight: 700;">$${item.subtotal.toFixed(2)}</div>
                </div>
                <div class="d-flex align-items-center gap-1">
                    <button class="btn btn-sm btn-outline-secondary" style="width:28px;height:28px;padding:0;" onclick="changeQty(${index}, -1); renderCartMobile();">-</button>
                    <span class="fw-bold small mx-1">${item.qty}</span>
                    <button class="btn btn-sm btn-outline-secondary" style="width:28px;height:28px;padding:0;" onclick="changeQty(${index}, 1); renderCartMobile();">+</button>
                    <button class="btn btn-sm text-danger" style="width:28px;height:28px;padding:0;font-size:0.7rem;" onclick="removeItem(${index}); renderCartMobile();"><i class="bi bi-x-lg"></i></button>
                </div>`;
            container.appendChild(div);
        });
    }

    let subtotal = cart.reduce((sum, i) => sum + i.subtotal, 0);
    let total = subtotal;
    if (appliedDiscount) {
        if (appliedDiscount.type === 'percentage') total = subtotal * (1 - appliedDiscount.value / 100);
        else total = subtotal - appliedDiscount.value;
        if (total < 0) total = 0;
    }
    document.getElementById('cart-subtotal-mobile').textContent = subtotal.toFixed(2);
    document.getElementById('cart-total-mobile').textContent = total.toFixed(2);
    document.getElementById('discount-msg-mobile').textContent = appliedDiscount ? appliedDiscount.message : '';
    updateCartBadge();
}

async function applyDiscountMobile() {
    const code = document.getElementById('discount-input-mobile').value.trim().toUpperCase();
    if (!code) return;
    const disc = await db.discounts.where('code').equals(code).first();
    if (disc) {
        appliedDiscount = { type: disc.discount_type, value: disc.value, message: disc.discount_type === 'percentage' ? disc.value + '% off' : '$' + disc.value.toFixed(2) + ' off' };
    } else {
        appliedDiscount = null;
        document.getElementById('discount-msg-mobile').textContent = 'Invalid code';
        document.getElementById('discount-msg-mobile').style.color = '#dc3545';
    }
    renderCart();
    renderCartMobile();
}

async function completeSaleMobile() {
    if (cart.length === 0) return showToast('Add items to cart first!', true);
    const payment = document.querySelector('input[name="payment_m"]:checked').value;

    let subtotal = cart.reduce((sum, i) => sum + i.subtotal, 0);
    let discountAmount = 0;
    if (appliedDiscount) {
        if (appliedDiscount.type === 'percentage') discountAmount = subtotal * (appliedDiscount.value / 100);
        else discountAmount = appliedDiscount.value;
    }
    let total = Math.max(0, subtotal - discountAmount);

    if (!confirm('Complete sale for $' + total.toFixed(2) + ' (' + payment + ')?')) return;

    const now = new Date().toISOString().replace('T', ' ').slice(0, 19);
    const saleId = Date.now();

    await db.sales.add({
        id: saleId, user_id: currentUser.id, total, discount_amount: discountAmount,
        payment_method: payment, created_at: now
    });

    for (const item of cart) {
        await db.sale_items.add({
            id: Date.now() + Math.random(), sale_id: saleId, product_id: item.product_id,
            qty: item.qty, unit_price: item.unit_price, subtotal: item.subtotal
        });
        const product = await db.products.get(item.product_id);
        if (product) await db.products.update(item.product_id, { stock_qty: (product.stock_qty || 0) - item.qty });
        await db.inventory.where('product_id').equals(item.product_id).modify(i => { i.stock_qty = Math.max(0, i.stock_qty - item.qty); });
    }

    await db.pending_sync.add({ type: 'sale', data: { sale_id: saleId, user_id: currentUser.id, total, discount_amount: discountAmount, payment_method: payment, items: cart } });

    const user = await db.users.get(currentUser.id);
    const saleIdShort = String(saleId).slice(-6);
    const receiptHtml = buildReceiptHtml(saleIdShort, now, user ? user.full_name : 'Unknown', payment, cart, discountAmount, total);

    showToast('Sale #' + saleIdShort + ' completed!');
    cart = [];
    appliedDiscount = null;
    document.getElementById('discount-input-mobile').value = '';
    document.getElementById('discount-msg-mobile').textContent = '';
    renderCart();
    renderCartMobile();
    filterProducts();
    toggleMobileCart();
    showReceiptModal(saleIdShort, receiptHtml);
}

// ========== ANALYTICS ==========
async function loadAnalytics() {
    const allSales = await db.sales.toArray();
    const allItems = await db.sale_items.toArray();
    const products = await db.products.toArray();
    const users = await db.users.toArray();
    const cats = await db.categories.toArray();

    const prodMap = {}, userMap = {}, catMap = {};
    products.forEach(p => prodMap[p.id] = p);
    users.forEach(u => userMap[u.id] = u);
    cats.forEach(c => catMap[c.id] = c.name);

    const totalRev = allSales.reduce((s, x) => s + x.total, 0);
    const totalDisc = allSales.reduce((s, x) => s + x.discount_amount, 0);
    const totalCost = allItems.reduce((s, x) => {
        const p = prodMap[x.product_id];
        return s + ((p ? p.cost || 0 : 0) * x.qty);
    }, 0);
    const totalProfit = totalRev - totalCost;
    const avgOrder = allSales.length > 0 ? totalRev / allSales.length : 0;

    document.getElementById('an-revenue').textContent = '$' + totalRev.toFixed(2);
    document.getElementById('an-profit').textContent = '$' + totalProfit.toFixed(2);
    document.getElementById('an-orders').textContent = allSales.length;
    document.getElementById('an-avg').textContent = '$' + avgOrder.toFixed(2);
    document.getElementById('an-disc').textContent = '$' + totalDisc.toFixed(2);
    document.getElementById('an-products').textContent = products.length;

    const staffSales = {};
    allSales.forEach(s => {
        if (!staffSales[s.user_id]) staffSales[s.user_id] = { count: 0, total: 0 };
        staffSales[s.user_id].count++;
        staffSales[s.user_id].total += s.total;
    });
    let staffHtml = '';
    Object.entries(staffSales).sort((a, b) => b[1].total - a[1].total).forEach(([uid, data]) => {
        const u = userMap[uid];
        staffHtml += `<div class="d-flex justify-content-between py-2 border-bottom small">
            <span>${u ? u.full_name : 'Unknown'}</span>
            <span><span class="text-muted">${data.count} orders</span> <span class="fw-bold" style="color:var(--nav-bg);">$${data.total.toFixed(2)}</span></span>
        </div>`;
    });
    document.getElementById('analytics-staff').innerHTML = staffHtml || '<p class="text-muted small">No data</p>';

    const payMethods = {};
    allSales.forEach(s => {
        if (!payMethods[s.payment_method]) payMethods[s.payment_method] = 0;
        payMethods[s.payment_method] += s.total;
    });
    let payHtml = '';
    Object.entries(payMethods).sort((a, b) => b[1] - a[1]).forEach(([method, amt]) => {
        const pct = totalRev > 0 ? Math.round((amt / totalRev) * 100) : 0;
        payHtml += `<div class="mb-2">
            <div class="d-flex justify-content-between small"><span>${method}</span><span class="fw-bold">$${amt.toFixed(2)} (${pct}%)</span></div>
            <div class="progress" style="height: 6px;"><div class="progress-bar" style="width:${pct}%;background:var(--nav-bg);"></div></div>
        </div>`;
    });
    document.getElementById('analytics-payments').innerHTML = payHtml || '<p class="text-muted small">No data</p>';

    const catSales = {};
    allItems.forEach(si => {
        const p = prodMap[si.product_id];
        if (p) {
            const catName = catMap[p.category_id] || 'Uncategorized';
            if (!catSales[catName]) catSales[catName] = { qty: 0, revenue: 0 };
            catSales[catName].qty += si.qty;
            catSales[catName].revenue += si.subtotal;
        }
    });
    let catHtml = '';
    Object.entries(catSales).sort((a, b) => b[1].revenue - a[1].revenue).forEach(([cat, data]) => {
        catHtml += `<div class="d-flex justify-content-between py-2 border-bottom small">
            <span>${cat}</span>
            <span><span class="text-muted">${data.qty} units</span> <span class="fw-bold" style="color:var(--nav-bg);">$${data.revenue.toFixed(2)}</span></span>
        </div>`;
    });
    document.getElementById('analytics-categories').innerHTML = catHtml || '<p class="text-muted small">No data</p>';

    const hourly = Array(24).fill(0);
    allSales.forEach(s => {
        if (s.created_at) {
            const h = parseInt(s.created_at.split(' ')[1]?.split(':')[0]);
            if (!isNaN(h)) hourly[h] += s.total;
        }
    });
    drawHourlyChart(hourly);
}

function drawHourlyChart(hourly) {
    const canvas = document.getElementById('chart-hourly');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    canvas.width = canvas.offsetWidth * dpr;
    canvas.height = 180 * dpr;
    ctx.scale(dpr, dpr);
    const w = canvas.offsetWidth, h = 180;
    ctx.clearRect(0, 0, w, h);

    const active = hourly.filter(v => v > 0);
    if (active.length === 0) {
        ctx.fillStyle = '#888';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('No hourly data', w / 2, h / 2);
        return;
    }

    const maxVal = Math.max(...hourly, 1);
    const margin = 40;
    const barW = Math.max(4, (w - margin * 2) / 24 - 2);
    const chartH = h - margin * 2;

    hourly.forEach((val, i) => {
        const x = margin + i * (barW + 2);
        const barH = (val / maxVal) * chartH;
        const y1 = h - margin;
        const y2 = y1 - barH;
        ctx.fillStyle = val > 0 ? '#166534' : '#e0e0e0';
        ctx.fillRect(x, y2, barW, barH);
        if (i % 3 === 0) {
            ctx.fillStyle = '#888';
            ctx.font = '9px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(i + ':00', x + barW / 2, y1 + 12);
        }
        if (val > 0) {
            ctx.fillStyle = '#166534';
            ctx.font = 'bold 8px sans-serif';
            ctx.fillText('$' + val.toFixed(0), x + barW / 2, y2 - 4);
        }
    });
}

// ========== INIT ==========
async function init() {
    await syncFromServer();
    loadStaff();
    setInterval(syncFromServer, 30000);
    window.addEventListener('online', () => {
        syncFromServer();
        syncPendingToServer();
    });
}

init();
