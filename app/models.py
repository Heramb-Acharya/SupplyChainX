from datetime import datetime, timezone
from app.database import db


class Supplier(db.Model):
    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    contact_person = db.Column(db.String(120))
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(30))
    address = db.Column(db.String(250))
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    products = db.relationship("Product", backref="supplier", lazy=True)
    purchase_orders = db.relationship(
        "PurchaseOrder", backref="supplier", lazy=True
    )


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80))
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    reorder_level = db.Column(db.Integer, nullable=False, default=10)
    unit_price = db.Column(db.Float, nullable=False, default=0.0)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"))
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )


class PurchaseOrder(db.Model):
    __tablename__ = "purchase_orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(40), unique=True, nullable=False)
    supplier_id = db.Column(
        db.Integer, db.ForeignKey("suppliers.id"), nullable=False
    )
    status = db.Column(db.String(30), nullable=False, default="Pending")
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    items = db.relationship(
        "OrderItem", backref="purchase_order",
        cascade="all, delete-orphan", lazy=True
    )
    shipment = db.relationship(
        "Shipment", backref="purchase_order",
        uselist=False, cascade="all, delete-orphan"
    )


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer, db.ForeignKey("purchase_orders.id"), nullable=False
    )
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id"), nullable=False
    )
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)

    product = db.relationship("Product")


class Shipment(db.Model):
    __tablename__ = "shipments"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer, db.ForeignKey("purchase_orders.id"),
        nullable=False, unique=True
    )
    tracking_number = db.Column(db.String(80), unique=True)
    carrier = db.Column(db.String(100))
    status = db.Column(db.String(30), nullable=False, default="Processing")
    estimated_delivery = db.Column(db.Date)
    delivered_at = db.Column(db.DateTime)


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
