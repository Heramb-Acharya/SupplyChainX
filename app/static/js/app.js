const API = "/api";

const $ = (id) => document.getElementById(id);

let products = [];
let suppliers = [];
let orders = [];
let shipments = [];
let activities = [];

document.addEventListener("DOMContentLoaded", () => {
    $("current-date").textContent = new Date().toLocaleDateString(
        "en-IN",
        { day: "numeric", month: "short", year: "numeric" }
    );

    document.querySelectorAll(".nav-item").forEach(button => {
        button.addEventListener("click", () => showSection(button.dataset.section));
    });

    loadAll();
});

async function api(path, options = {}) {
    const response = await fetch(`${API}${path}`, {
        headers: { "Content-Type": "application/json" },
        ...options
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.error || data.message || "Request failed");
    }

    return data;
}

async function loadAll() {
    try {
        const results = await Promise.all([
            api("/dashboard"),
            api("/products"),
            api("/suppliers"),
            api("/orders"),
            api("/shipments"),
            api("/activities")
        ]);

        products = results[1];
        suppliers = results[2];
        populateProductOptions();
        orders = results[3];
        shipments = results[4];
        activities = results[5];

        renderDashboard(results[0]);
        renderProducts();
        renderSuppliers();
        renderOrders();
        renderShipments();
        renderActivities();
    } catch (error) {
        console.error(error);
        showToast(`Unable to load data: ${error.message}`);
    }
}

function showSection(section) {
    document.querySelectorAll(".page-section").forEach(item => {
        item.classList.remove("active");
    });

    document.querySelectorAll(".nav-item").forEach(item => {
        item.classList.toggle("active", item.dataset.section === section);
    });

    $(`${section}-section`).classList.add("active");

    const labels = {
        dashboard: "Dashboard",
        inventory: "Inventory",
        suppliers: "Suppliers",
        orders: "Purchase Orders",
        shipments: "Shipments",
        activities: "Activity Log"
    };

    $("breadcrumb-current").textContent = labels[section] || section;
}

function renderDashboard(data) {
    $("stat-products").textContent = data.total_products ?? products.length;
    $("stat-suppliers").textContent = data.total_suppliers ?? suppliers.length;
    $("stat-orders").textContent = data.pending_orders ?? 0;
    $("stat-low-stock").textContent = data.low_stock_count ?? data.low_stock ?? 0;

    const lowStock = products
        .filter(p => Number(p.quantity) <= Number(p.reorder_level))
        .slice(0, 6);

    $("dashboard-inventory").innerHTML = lowStock.length
        ? lowStock.map(p => `
            <tr>
                <td>${escapeHTML(p.name)}</td>
                <td>${escapeHTML(p.sku)}</td>
                <td>${p.quantity}</td>
                <td>${statusBadge("Low Stock")}</td>
            </tr>
        `).join("")
        : `<tr><td colspan="4" class="empty-state">No low-stock products. Inventory looks good.</td></tr>`;

    $("dashboard-activities").innerHTML = activities.length
        ? activities.slice(0, 5).map(activityHTML).join("")
        : `<div class="empty-state">No recent activity.</div>`;
}

function renderProducts() {
    $("product-table").innerHTML = products.length
        ? products.map(p => `
            <tr>
                <td>${escapeHTML(p.name)}</td>
                <td>${escapeHTML(p.sku)}</td>
                <td>${escapeHTML(p.category || "—")}</td>
                <td>${p.quantity}</td>
                <td>${p.reorder_level}</td>
                <td>${money(p.unit_price)}</td>
                <td>${statusBadge(Number(p.quantity) <= Number(p.reorder_level) ? "Low Stock" : "In Stock")}</td>
                <td>
                    <button class="action-button" onclick="editProduct(${p.id})">Edit</button>
                    <button class="action-button delete" onclick="deleteProduct(${p.id})">Delete</button>
                </td>
            </tr>
        `).join("")
        : emptyRow(8, "No products added yet.");
}

function renderSuppliers() {
    $("supplier-table").innerHTML = suppliers.length
        ? suppliers.map(s => `
            <tr>
                <td>${escapeHTML(s.name)}</td>
                <td>${escapeHTML(s.contact_person || "—")}</td>
                <td>${escapeHTML(s.email || "—")}</td>
                <td>${escapeHTML(s.phone || "—")}</td>
                <td>
                    <button class="action-button" onclick="editSupplier(${s.id})">Edit</button>
                    <button class="action-button delete" onclick="deleteSupplier(${s.id})">Delete</button>
                </td>
            </tr>
        `).join("")
        : emptyRow(5, "No suppliers registered yet.");
}

function renderOrders() {
    $("order-table").innerHTML = orders.length
        ? orders.map(o => `
            <tr>
                <td>${escapeHTML(o.order_number)}</td>
                <td>${escapeHTML(o.supplier_name || "—")}</td>
                <td>${formatDate(o.created_at)}</td>
                <td>${o.items?.length || 0}</td>
                <td>${money(o.total_amount)}</td>
                <td>${statusBadge(o.status)}</td>
                <td>
                    <button class="action-button" onclick="updateOrderStatus(${o.id})">Update Status</button>
                    <button class="action-button delete" onclick="deleteOrder(${o.id})">Delete</button>
                </td>
            </tr>
        `).join("")
        : emptyRow(7, "No purchase orders created yet.");
}

function renderShipments() {
    $("shipment-table").innerHTML = shipments.length
        ? shipments.map(s => `
            <tr>
                <td>${escapeHTML(s.order_number || "—")}</td>
                <td>${escapeHTML(s.tracking_number || "—")}</td>
                <td>${escapeHTML(s.carrier || "—")}</td>
                <td>${statusBadge(s.status)}</td>
                <td>${s.estimated_delivery ? formatDate(s.estimated_delivery) : "—"}</td>
                <td>
                    <button class="action-button" onclick="updateShipmentStatus(${s.id})">Update Status</button>
                    <button class="action-button delete" onclick="deleteShipment(${s.id})">Delete</button>
                </td>
            </tr>
        `).join("")
        : emptyRow(6, "No shipments registered yet.");
}

function renderActivities() {
    $("activity-table").innerHTML = activities.length
        ? activities.map(activityHTML).join("")
        : `<div class="empty-state">No activity recorded yet.</div>`;
}

function activityHTML(a) {
    return `
        <div class="activity-item">
            <div class="activity-marker">↗</div>
            <div>
                <strong>${escapeHTML(a.action)}</strong>
                <p>${escapeHTML(a.description || "")}</p>
                <small>${formatDate(a.created_at)}</small>
            </div>
        </div>
    `;
}

function statusBadge(status) {
    const value = String(status || "Unknown");
    const lower = value.toLowerCase();

    let type = "neutral";
    if (["delivered", "in stock", "completed"].includes(lower)) type = "success";
    else if (["pending", "processing", "low stock", "in transit"].includes(lower)) type = "warning";
    else if (["cancelled", "failed"].includes(lower)) type = "danger";

    return `<span class="status-badge ${type}">${escapeHTML(value)}</span>`;
}

function emptyRow(columns, message) {
    return `<tr><td colspan="${columns}" class="empty-state">${message}</td></tr>`;
}

function money(value) {
    return Number(value || 0).toLocaleString("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 2
    });
}

function formatDate(value) {
    if (!value) return "—";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? escapeHTML(value) :
        date.toLocaleDateString("en-IN", {
            day: "2-digit", month: "short", year: "numeric"
        });
}

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[char]);
}

function showToast(message) {
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = message;
    $("toast-container").appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
}

function filterTable(tableId, query) {
    const search = query.toLowerCase();
    document.querySelectorAll(`#${tableId} tr`).forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(search) ? "" : "none";
    });
}

/* Modal helpers */

function openModal(id) {
    const modal = $(id);
    if (!modal) {
        showToast("Form interface is being prepared.");
        return;
    }
    modal.classList.add("open");
}

function closeModal(id) {
    $(id)?.classList.remove("open");
}

function formData(form) {
    return Object.fromEntries(new FormData(form).entries());
}

/* Product operations */

async function saveProduct(event) {
    event.preventDefault();
    const form = event.target;
    const id = form.dataset.editId;

    const payload = formData(form);
    ["quantity", "reorder_level", "unit_price", "supplier_id"].forEach(key => {
        if (payload[key] !== undefined && payload[key] !== "") {
            payload[key] = Number(payload[key]);
        }
    });

    try {
        await api(id ? `/products/${id}` : "/products", {
            method: id ? "PUT" : "POST",
            body: JSON.stringify(payload)
        });
        form.reset();
        delete form.dataset.editId;
        closeModal("product-modal");
        await loadAll();
        showToast(id ? "Product updated successfully." : "Product added successfully.");
    } catch (error) {
        showToast(error.message);
    }
}

function editProduct(id) {
    const product = products.find(p => p.id === id);
    if (!product) return;
    populateProductOptions();
    const form = $("product-form");
    form.dataset.editId = id;
    Object.entries(product).forEach(([key, value]) => {
        if (form.elements[key]) form.elements[key].value = value ?? "";
    });
    openModal("product-modal");
}

async function deleteProduct(id) {
    if (!confirm("Delete this product?")) return;
    try {
        await api(`/products/${id}`, { method: "DELETE" });
        await loadAll();
        showToast("Product deleted.");
    } catch (error) {
        showToast(error.message);
    }
}

/* Supplier operations */

async function saveSupplier(event) {
    event.preventDefault();
    const form = event.target;
    const id = form.dataset.editId;

    try {
        await api(id ? `/suppliers/${id}` : "/suppliers", {
            method: id ? "PUT" : "POST",
            body: JSON.stringify(formData(form))
        });
        form.reset();
        delete form.dataset.editId;
        closeModal("supplier-modal");
        await loadAll();
        showToast(id ? "Supplier updated." : "Supplier added.");
    } catch (error) {
        showToast(error.message);
    }
}

function editSupplier(id) {
    const supplier = suppliers.find(s => s.id === id);
    if (!supplier) return;
    const form = $("supplier-form");
    form.dataset.editId = id;
    Object.entries(supplier).forEach(([key, value]) => {
        if (form.elements[key]) form.elements[key].value = value ?? "";
    });
    openModal("supplier-modal");
}

async function deleteSupplier(id) {
    if (!confirm("Delete this supplier?")) return;
    try {
        await api(`/suppliers/${id}`, { method: "DELETE" });
        await loadAll();
        showToast("Supplier deleted.");
    } catch (error) {
        showToast(error.message);
    }
}

/* Purchase order operations */

function populateProductOptions() {
    const select = $("product-supplier");
    if (!select) return;

    select.innerHTML =
        '<option value="">No supplier assigned</option>' +
        suppliers.map(s =>
            `<option value="${s.id}">${escapeHTML(s.name)}</option>`
        ).join("");
}

function populateOrderOptions() {
    const supplierSelect = $("order-supplier");
    const productSelect = $("order-product");

    supplierSelect.innerHTML = suppliers.map(s =>
        `<option value="${s.id}">${escapeHTML(s.name)}</option>`
    ).join("");

    productSelect.innerHTML = products.map(p =>
        `<option value="${p.id}" data-price="${p.unit_price}">${escapeHTML(p.name)} (${escapeHTML(p.sku)})</option>`
    ).join("");
}

async function saveOrder(event) {
    event.preventDefault();

    const supplier_id = Number($("order-supplier").value);
    const product_id = Number($("order-product").value);
    const quantity = Number($("order-quantity").value);
    const selected = products.find(p => p.id === product_id);

    if (!supplier_id || !selected || quantity <= 0) {
        showToast("Select a supplier, product and valid quantity.");
        return;
    }

    try {
        await api("/orders", {
            method: "POST",
            body: JSON.stringify({
                supplier_id,
                items: [{ product_id, quantity }]
            })
        });
        $("order-form").reset();
        closeModal("order-modal");
        await loadAll();
        showToast("Purchase order created.");
    } catch (error) {
        showToast(error.message);
    }
}

async function updateOrderStatus(id) {
    const status = prompt("Enter status: Pending, Processing, Dispatched, Delivered or Cancelled");
    if (!status) return;

    try {
        await api(`/orders/${id}`, {
            method: "PUT",
            body: JSON.stringify({ status })
        });
        await loadAll();
        showToast("Order status updated.");
    } catch (error) {
        showToast(error.message);
    }
}

async function deleteOrder(id) {
    if (!confirm("Delete this purchase order?")) return;
    try {
        await api(`/orders/${id}`, { method: "DELETE" });
        await loadAll();
        showToast("Purchase order deleted.");
    } catch (error) {
        showToast(error.message);
    }
}

/* Shipment operations */

function populateShipmentOptions() {
    const select = $("shipment-order");
    const available = orders.filter(o =>
        !shipments.some(s => s.order_id === o.id)
    );

    select.innerHTML = available.map(o =>
        `<option value="${o.id}">${escapeHTML(o.order_number)}</option>`
    ).join("");
}

async function saveShipment(event) {
    event.preventDefault();

    const payload = formData(event.target);
    payload.order_id = Number(payload.order_id);

    try {
        await api("/shipments", {
            method: "POST",
            body: JSON.stringify(payload)
        });
        event.target.reset();
        closeModal("shipment-modal");
        await loadAll();
        showToast("Shipment registered.");
    } catch (error) {
        showToast(error.message);
    }
}

async function updateShipmentStatus(id) {
    const status = prompt("Enter status: Processing, Dispatched, In Transit or Delivered");
    if (!status) return;

    try {
        await api(`/shipments/${id}`, {
            method: "PUT",
            body: JSON.stringify({ status })
        });
        await loadAll();
        showToast("Shipment status updated.");
    } catch (error) {
        showToast(error.message);
    }
}

async function deleteShipment(id) {
    if (!confirm("Delete this shipment?")) return;
    try {
        await api(`/shipments/${id}`, { method: "DELETE" });
        await loadAll();
        showToast("Shipment deleted.");
    } catch (error) {
        showToast(error.message);
    }
}

/* Populate dropdowns whenever a modal is opened */

document.addEventListener("click", event => {
    const button = event.target.closest("button");
    if (!button) return;

    if (button.getAttribute("onclick")?.includes("order-modal")) {
        populateOrderOptions();
    }

    if (button.getAttribute("onclick")?.includes("shipment-modal")) {
        populateShipmentOptions();
    }
});
