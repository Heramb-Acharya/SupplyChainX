from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, render_template
from sqlalchemy import func
from app.database import db
from app.models import (
    Product, Supplier, PurchaseOrder,
    OrderItem, Shipment, ActivityLog
)

main = Blueprint("main", __name__)


def log_activity(action, description, entity_type=None, entity_id=None):
    entry = ActivityLog(
        action=action,
        description=description,
        entity_type=entity_type,
        entity_id=entity_id
    )
    db.session.add(entry)


def error(message, status=400):
    return jsonify({"error": message}), status


def get_payload():
    return request.get_json(silent=True) or {}


def product_dict(p):
    return {
        "id": p.id,
        "sku": p.sku,
        "name": p.name,
        "category": p.category,
        "description": p.description,
        "quantity": p.quantity,
        "reorder_level": p.reorder_level,
        "unit_price": p.unit_price,
        "supplier_id": p.supplier_id,
        "supplier_name": p.supplier.name if p.supplier else None,
        "low_stock": p.quantity <= p.reorder_level
    }


def supplier_dict(s):
    return {
        "id": s.id,
        "name": s.name,
        "contact_person": s.contact_person,
        "email": s.email,
        "phone": s.phone,
        "address": s.address
    }


def order_dict(o):
    return {
        "id": o.id,
        "order_number": o.order_number,
        "supplier_id": o.supplier_id,
        "supplier_name": o.supplier.name,
        "status": o.status,
        "total_amount": o.total_amount,
        "created_at": o.created_at.isoformat() if o.created_at else None,
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product.name,
                "quantity": item.quantity,
                "unit_price": item.unit_price
            }
            for item in o.items
        ]
    }


def shipment_dict(s):
    return {
        "id": s.id,
        "order_id": s.order_id,
        "order_number": s.purchase_order.order_number,
        "tracking_number": s.tracking_number,
        "carrier": s.carrier,
        "status": s.status,
        "estimated_delivery": (
            s.estimated_delivery.isoformat()
            if s.estimated_delivery else None
        ),
        "delivered_at": (
            s.delivered_at.isoformat() if s.delivered_at else None
        )
    }


@main.route("/")
def index():
    return render_template("index.html")


# -------------------- HEALTH CHECK --------------------

@main.route("/api/health", methods=["GET"])
def health():
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify({
            "status": "healthy",
            "application": "SupplyChainX",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200
    except Exception:
        db.session.rollback()
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected"
        }), 503


# -------------------- DASHBOARD --------------------

@main.route("/api/dashboard", methods=["GET"])
def dashboard():
    total_products = Product.query.count()
    total_suppliers = Supplier.query.count()
    total_orders = PurchaseOrder.query.count()
    low_stock = Product.query.filter(
        Product.quantity <= Product.reorder_level
    ).count()

    pending_orders = PurchaseOrder.query.filter(
        PurchaseOrder.status.in_(["Pending", "Processing"])
    ).count()

    delivered_orders = PurchaseOrder.query.filter_by(
        status="Delivered"
    ).count()

    recent_activities = ActivityLog.query.order_by(
        ActivityLog.created_at.desc()
    ).limit(8).all()

    return jsonify({
        "total_products": total_products,
        "total_suppliers": total_suppliers,
        "total_orders": total_orders,
        "low_stock": low_stock,
        "pending_orders": pending_orders,
        "delivered_orders": delivered_orders,
        "recent_activities": [
            {
                "action": a.action,
                "description": a.description,
                "created_at": a.created_at.isoformat()
                if a.created_at else None
            }
            for a in recent_activities
        ]
    })


# -------------------- PRODUCTS --------------------

@main.route("/api/products", methods=["GET", "POST"])
def products():
    if request.method == "GET":
        items = Product.query.order_by(Product.id.desc()).all()
        return jsonify([product_dict(p) for p in items])

    data = get_payload()
    sku = str(data.get("sku", "")).strip()
    name = str(data.get("name", "")).strip()

    if not sku or not name:
        return error("SKU and product name are required")

    try:
        quantity = int(data.get("quantity", 0))
        reorder_level = int(data.get("reorder_level", 10))
        unit_price = float(data.get("unit_price", 0))
        supplier_id = data.get("supplier_id") or None

        if quantity < 0 or reorder_level < 0 or unit_price < 0:
            return error("Quantity, reorder level and price cannot be negative")

        if supplier_id is not None:
            supplier = db.session.get(Supplier, int(supplier_id))
            if not supplier:
                return error("Supplier not found", 404)

        product = Product(
            sku=sku,
            name=name,
            category=data.get("category"),
            description=data.get("description"),
            quantity=quantity,
            reorder_level=reorder_level,
            unit_price=unit_price,
            supplier_id=int(supplier_id) if supplier_id else None
        )

        db.session.add(product)
        db.session.flush()
        log_activity("Product added", f"Added product {name}", "Product", product.id)
        db.session.commit()
        return jsonify(product_dict(product)), 201

    except (ValueError, TypeError):
        db.session.rollback()
        return error("Invalid numeric value")
    except Exception:
        db.session.rollback()
        return error("Could not create product. Check for duplicate SKU.")


@main.route("/api/products/<int:product_id>", methods=["GET", "PUT", "DELETE"])
def product_detail(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return error("Product not found", 404)

    if request.method == "GET":
        return jsonify(product_dict(product))

    if request.method == "DELETE":
        name = product.name
        if OrderItem.query.filter_by(product_id=product_id).first():
            return error("Cannot delete a product referenced by an order")
        db.session.delete(product)
        log_activity("Product deleted", f"Deleted product {name}", "Product", product_id)
        db.session.commit()
        return jsonify({"message": "Product deleted"})

    data = get_payload()

    try:
        for field in ["sku", "name", "category", "description", "quantity",
                      "reorder_level", "unit_price", "supplier_id"]:
            if field in data:
                value = data[field]
                if field in ["quantity", "reorder_level"]:
                    value = int(value)
                    if value < 0:
                        return error(f"{field} cannot be negative")
                elif field == "unit_price":
                    value = float(value)
                    if value < 0:
                        return error("Price cannot be negative")
                elif field == "supplier_id":
                    if value in (None, ""):
                        value = None
                    else:
                        value = int(value)
                        if not db.session.get(Supplier, value):
                            return error("Supplier not found", 404)
                elif field in ["sku", "name"]:
                    value = str(value).strip()
                    if not value:
                        return error(f"{field} cannot be empty")
                setattr(product, field, value)

        log_activity("Product updated", f"Updated product {product.name}", "Product", product.id)
        db.session.commit()
        return jsonify(product_dict(product))

    except (ValueError, TypeError):
        db.session.rollback()
        return error("Invalid field value")
    except Exception:
        db.session.rollback()
        return error("Could not update product. Check for duplicate SKU.")


# -------------------- SUPPLIERS --------------------

@main.route("/api/suppliers", methods=["GET", "POST"])
def suppliers():
    if request.method == "GET":
        return jsonify([
            supplier_dict(s)
            for s in Supplier.query.order_by(Supplier.id.desc()).all()
        ])

    data = get_payload()
    name = str(data.get("name", "")).strip()

    if not name:
        return error("Supplier name is required")

    supplier = Supplier(
        name=name,
        contact_person=data.get("contact_person"),
        email=data.get("email"),
        phone=data.get("phone"),
        address=data.get("address")
    )

    db.session.add(supplier)
    try:
        db.session.flush()
        log_activity("Supplier added", f"Added supplier {name}", "Supplier", supplier.id)
        db.session.commit()
        return jsonify(supplier_dict(supplier)), 201
    except Exception:
        db.session.rollback()
        return error("Could not create supplier. Check for duplicate email.")


@main.route("/api/suppliers/<int:supplier_id>", methods=["GET", "PUT", "DELETE"])
def supplier_detail(supplier_id):
    supplier = db.session.get(Supplier, supplier_id)
    if not supplier:
        return error("Supplier not found", 404)

    if request.method == "GET":
        return jsonify(supplier_dict(supplier))

    if request.method == "DELETE":
        if supplier.products or supplier.purchase_orders:
            return error("Cannot delete a supplier with linked products or orders")
        name = supplier.name
        db.session.delete(supplier)
        log_activity("Supplier deleted", f"Deleted supplier {name}", "Supplier", supplier_id)
        db.session.commit()
        return jsonify({"message": "Supplier deleted"})

    data = get_payload()
    for field in ["name", "contact_person", "email", "phone", "address"]:
        if field in data:
            if field == "name" and not str(data[field]).strip():
                return error("Supplier name cannot be empty")
            setattr(supplier, field, data[field])

    try:
        log_activity("Supplier updated", f"Updated supplier {supplier.name}", "Supplier", supplier.id)
        db.session.commit()
        return jsonify(supplier_dict(supplier))
    except Exception:
        db.session.rollback()
        return error("Could not update supplier. Check for duplicate email.")


# -------------------- PURCHASE ORDERS --------------------

@main.route("/api/orders", methods=["GET", "POST"])
def orders():
    if request.method == "GET":
        return jsonify([
            order_dict(o)
            for o in PurchaseOrder.query.order_by(
                PurchaseOrder.id.desc()
            ).all()
        ])

    data = get_payload()
    try:
        supplier_id = int(data.get("supplier_id"))
        supplier = db.session.get(Supplier, supplier_id)
        if not supplier:
            return error("Supplier not found", 404)

        items_data = data.get("items", [])
        if not isinstance(items_data, list) or not items_data:
            return error("At least one order item is required")

        order = PurchaseOrder(
            order_number=f"PO-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
            supplier_id=supplier_id,
            status="Pending",
            total_amount=0
        )
        db.session.add(order)
        db.session.flush()

        total = 0
        for entry in items_data:
            product = db.session.get(Product, int(entry["product_id"]))
            quantity = int(entry["quantity"])

            if not product:
                db.session.rollback()
                return error("Product not found", 404)
            if quantity <= 0:
                db.session.rollback()
                return error("Order quantities must be positive")

            item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=product.unit_price
            )
            db.session.add(item)
            total += quantity * product.unit_price

        order.total_amount = total
        log_activity("Order created", f"Created purchase order {order.order_number}", "Order", order.id)
        db.session.commit()
        return jsonify(order_dict(order)), 201

    except (ValueError, TypeError, KeyError):
        db.session.rollback()
        return error("Invalid order data")
    except Exception:
        db.session.rollback()
        return error("Could not create purchase order")


@main.route("/api/orders/<int:order_id>", methods=["GET", "PUT", "DELETE"])
def order_detail(order_id):
    order = db.session.get(PurchaseOrder, order_id)
    if not order:
        return error("Order not found", 404)

    if request.method == "GET":
        return jsonify(order_dict(order))

    if request.method == "DELETE":
        if order.shipment:
            return error("Delete the linked shipment before deleting this order")
        number = order.order_number
        db.session.delete(order)
        log_activity("Order deleted", f"Deleted purchase order {number}", "Order", order_id)
        db.session.commit()
        return jsonify({"message": "Order deleted"})

    data = get_payload()
    allowed = ["Pending", "Processing", "Dispatched", "Delivered", "Cancelled"]
    status = data.get("status")

    if status not in allowed:
        return error("Invalid order status")

    order.status = status
    log_activity("Order status updated", f"{order.order_number} status changed to {status}", "Order", order.id)
    db.session.commit()
    return jsonify(order_dict(order))


# -------------------- SHIPMENTS --------------------

@main.route("/api/shipments", methods=["GET", "POST"])
def shipments():
    if request.method == "GET":
        return jsonify([
            shipment_dict(s)
            for s in Shipment.query.order_by(Shipment.id.desc()).all()
        ])

    data = get_payload()
    try:
        order_id = int(data.get("order_id"))
        order = db.session.get(PurchaseOrder, order_id)

        if not order:
            return error("Order not found", 404)
        if order.shipment:
            return error("A shipment already exists for this order")

        shipment = Shipment(
            order_id=order_id,
            tracking_number=data.get("tracking_number"),
            carrier=data.get("carrier"),
            status="Processing"
        )
        db.session.add(shipment)
        log_activity("Shipment created", f"Shipment created for {order.order_number}", "Shipment", order_id)
        db.session.commit()
        return jsonify(shipment_dict(shipment)), 201

    except (ValueError, TypeError):
        db.session.rollback()
        return error("Invalid order ID")
    except Exception:
        db.session.rollback()
        return error("Could not create shipment. Check tracking number uniqueness.")


@main.route("/api/shipments/<int:shipment_id>", methods=["GET", "PUT", "DELETE"])
def shipment_detail(shipment_id):
    shipment = db.session.get(Shipment, shipment_id)
    if not shipment:
        return error("Shipment not found", 404)

    if request.method == "GET":
        return jsonify(shipment_dict(shipment))

    if request.method == "DELETE":
        db.session.delete(shipment)
        log_activity("Shipment deleted", "Shipment record deleted", "Shipment", shipment_id)
        db.session.commit()
        return jsonify({"message": "Shipment deleted"})

    data = get_payload()

    for field in ["tracking_number", "carrier"]:
        if field in data:
            setattr(shipment, field, data[field])

    if "status" in data:
        allowed = ["Processing", "Dispatched", "In Transit", "Delivered"]
        if data["status"] not in allowed:
            return error("Invalid shipment status")
        shipment.status = data["status"]

        if data["status"] == "Delivered":
            shipment.delivered_at = datetime.now(timezone.utc)
            shipment.purchase_order.status = "Delivered"
        elif data["status"] in ["Dispatched", "In Transit"]:
            shipment.purchase_order.status = "Dispatched"

    try:
        log_activity("Shipment updated", f"Shipment status: {shipment.status}", "Shipment", shipment.id)
        db.session.commit()
        return jsonify(shipment_dict(shipment))
    except Exception:
        db.session.rollback()
        return error("Could not update shipment. Check tracking number uniqueness.")


# -------------------- ACTIVITY LOG --------------------

@main.route("/api/activities", methods=["GET"])
def activities():
    entries = ActivityLog.query.order_by(
        ActivityLog.created_at.desc()
    ).limit(100).all()

    return jsonify([
        {
            "id": a.id,
            "action": a.action,
            "description": a.description,
            "entity_type": a.entity_type,
            "entity_id": a.entity_id,
            "created_at": a.created_at.isoformat() if a.created_at else None
        }
        for a in entries
    ])
