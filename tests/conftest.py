import pytest

from app import create_app
from app.database import db


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret"
    })

    with app.app_context():
        db.drop_all()
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def supplier(client):
    response = client.post("/api/suppliers", json={
        "name": "Test Supplier",
        "contact_person": "Test Contact",
        "email": "test@supplier.com",
        "phone": "9876543210",
        "address": "Chennai"
    })
    assert response.status_code == 201
    return response.get_json()


@pytest.fixture
def product(client, supplier):
    response = client.post("/api/products", json={
        "sku": "TEST-001",
        "name": "Test Sensor",
        "category": "Sensors",
        "quantity": 25,
        "reorder_level": 5,
        "unit_price": 1500,
        "supplier_id": supplier["id"]
    })
    assert response.status_code == 201
    return response.get_json()
