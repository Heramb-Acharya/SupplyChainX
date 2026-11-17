# -------------------- HEALTH AND DASHBOARD --------------------

def test_health_check(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_dashboard_initial_counts(client):
    response = client.get("/api/dashboard")

    assert response.status_code == 200
    data = response.get_json()
    assert data["total_products"] == 0
    assert data["total_suppliers"] == 0
    assert data["total_orders"] == 0


# -------------------- PRODUCT TESTS --------------------

def test_create_product(client, supplier):
    response = client.post("/api/products", json={
        "sku": "PROD-001",
        "name": "Pressure Sensor",
        "quantity": 20,
        "reorder_level": 5,
        "unit_price": 1200,
        "supplier_id": supplier["id"]
    })

    assert response.status_code == 201
    assert response.get_json()["name"] == "Pressure Sensor"
    assert response.get_json()["supplier_name"] == "Test Supplier"


def test_create_product_without_supplier(client):
    response = client.post("/api/products", json={
        "sku": "NO-SUP-001",
        "name": "Unassigned Sensor",
        "quantity": 10,
        "reorder_level": 5,
        "unit_price": 100,
        "supplier_id": ""
    })

    assert response.status_code == 201
    assert response.get_json()["supplier_name"] is None


def test_list_products(client, product):
    response = client.get("/api/products")

    assert response.status_code == 200
    assert len(response.get_json()) == 1


def test_get_product(client, product):
    response = client.get(f"/api/products/{product['id']}")

    assert response.status_code == 200
    assert response.get_json()["sku"] == "TEST-001"


def test_update_product(client, product):
    response = client.put(
        f"/api/products/{product['id']}",
        json={"quantity": 2}
    )

    assert response.status_code == 200
    assert response.get_json()["quantity"] == 2
    assert response.get_json()["low_stock"] is True


def test_delete_product(client, product):
    response = client.delete(f"/api/products/{product['id']}")

    assert response.status_code == 200
    assert client.get(f"/api/products/{product['id']}").status_code == 404


def test_product_requires_sku_and_name(client):
    response = client.post("/api/products", json={
        "quantity": 10
    })

    assert response.status_code == 400


def test_product_rejects_negative_quantity(client):
    response = client.post("/api/products", json={
        "sku": "NEG-001",
        "name": "Invalid Product",
        "quantity": -5
    })

    assert response.status_code == 400


def test_duplicate_product_sku_rejected(client, supplier):
    payload = {
        "sku": "DUP-001",
        "name": "First Product",
        "supplier_id": supplier["id"]
    }

    assert client.post("/api/products", json=payload).status_code == 201
    assert client.post("/api/products", json={
        **payload, "name": "Duplicate Product"
    }).status_code == 400


def test_missing_product_returns_404(client):
    assert client.get("/api/products/999").status_code == 404


# -------------------- SUPPLIER TESTS --------------------

def test_create_supplier(client):
    response = client.post("/api/suppliers", json={
        "name": "New Supplier",
        "email": "new@supplier.com"
    })

    assert response.status_code == 201
    assert response.get_json()["name"] == "New Supplier"


def test_list_suppliers(client, supplier):
    response = client.get("/api/suppliers")

    assert response.status_code == 200
    assert len(response.get_json()) == 1


def test_update_supplier(client, supplier):
    response = client.put(
        f"/api/suppliers/{supplier['id']}",
        json={"name": "Updated Supplier"}
    )

    assert response.status_code == 200
    assert response.get_json()["name"] == "Updated Supplier"


def test_duplicate_supplier_email_rejected(client):
    payload = {
        "name": "Supplier One",
        "email": "duplicate@supplier.com"
    }

    assert client.post("/api/suppliers", json=payload).status_code == 201
    assert client.post("/api/suppliers", json={
        "name": "Supplier Two",
        "email": "duplicate@supplier.com"
    }).status_code == 400


def test_supplier_with_linked_product_cannot_be_deleted(client, supplier, product):
    response = client.delete(f"/api/suppliers/{supplier['id']}")

    assert response.status_code == 400


def test_missing_supplier_returns_404(client):
    assert client.get("/api/suppliers/999").status_code == 404


# -------------------- PURCHASE ORDER TESTS --------------------

def test_create_purchase_order(client, supplier, product):
    response = client.post("/api/orders", json={
        "supplier_id": supplier["id"],
        "items": [
            {
                "product_id": product["id"],
                "quantity": 3
            }
        ]
    })

    assert response.status_code == 201
    data = response.get_json()
    assert data["status"] == "Pending"
    assert data["total_amount"] == 4500


def test_order_requires_items(client, supplier):
    response = client.post("/api/orders", json={
        "supplier_id": supplier["id"],
        "items": []
    })

    assert response.status_code == 400


def test_update_order_status(client, supplier, product):
    created = client.post("/api/orders", json={
        "supplier_id": supplier["id"],
        "items": [{"product_id": product["id"], "quantity": 2}]
    }).get_json()

    response = client.put(
        f"/api/orders/{created['id']}",
        json={"status": "Processing"}
    )

    assert response.status_code == 200
    assert response.get_json()["status"] == "Processing"


def test_invalid_order_status_rejected(client, supplier, product):
    created = client.post("/api/orders", json={
        "supplier_id": supplier["id"],
        "items": [{"product_id": product["id"], "quantity": 1}]
    }).get_json()

    response = client.put(
        f"/api/orders/{created['id']}",
        json={"status": "Unknown"}
    )

    assert response.status_code == 400


# -------------------- SHIPMENT TESTS --------------------

def test_create_and_update_shipment(client, supplier, product):
    order = client.post("/api/orders", json={
        "supplier_id": supplier["id"],
        "items": [{"product_id": product["id"], "quantity": 2}]
    }).get_json()

    response = client.post("/api/shipments", json={
        "order_id": order["id"],
        "tracking_number": "TRACK-001",
        "carrier": "Demo Logistics"
    })

    assert response.status_code == 201
    shipment = response.get_json()

    updated = client.put(
        f"/api/shipments/{shipment['id']}",
        json={"status": "Delivered"}
    )

    assert updated.status_code == 200
    assert updated.get_json()["status"] == "Delivered"

    updated_order = client.get(f"/api/orders/{order['id']}").get_json()
    assert updated_order["status"] == "Delivered"


def test_shipment_requires_valid_order(client):
    response = client.post("/api/shipments", json={
        "order_id": 999,
        "tracking_number": "TRACK-999"
    })

    assert response.status_code == 404


def test_duplicate_shipment_for_order_rejected(client, supplier, product):
    order = client.post("/api/orders", json={
        "supplier_id": supplier["id"],
        "items": [{"product_id": product["id"], "quantity": 1}]
    }).get_json()

    payload = {
        "order_id": order["id"],
        "tracking_number": "TRACK-002"
    }

    assert client.post("/api/shipments", json=payload).status_code == 201
    assert client.post("/api/shipments", json={
        **payload, "tracking_number": "TRACK-003"
    }).status_code == 400


# -------------------- ACTIVITY LOG AND LOW STOCK --------------------

def test_activity_log_records_product_creation(client, product):
    response = client.get("/api/activities")

    assert response.status_code == 200
    assert any(
        entry["action"] == "Product added"
        for entry in response.get_json()
    )


def test_dashboard_counts_low_stock_products(client, product):
    client.put(
        f"/api/products/{product['id']}",
        json={"quantity": 2}
    )

    response = client.get("/api/dashboard")

    assert response.status_code == 200
    assert response.get_json()["low_stock"] == 1
