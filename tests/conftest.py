import os

os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base, get_db
from app.main import app
from app.security import hash_api_key

ADMIN_KEY = "test-admin-key"

test_engine = create_engine("sqlite://",
                            connect_args={"check_same_thread": False},
                            poolclass=StaticPool)
TestingSession = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.create_all(bind=test_engine)
    with TestingSession() as db:
        db.add(models.Admin(username="admin", api_key_hash=hash_api_key(ADMIN_KEY)))
        db.commit()
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def admin_headers():
    return {"X-Admin-Key": ADMIN_KEY}


@pytest.fixture
def make_product(client, admin_headers):
    def _make(name="Petrol 95", price="500.00", litres="1000.00"):
        r = client.post("/api/admin/products/",
                        json={"name": name, "price_per_litre": price, "available_litres": litres},
                        headers=admin_headers)
        assert r.status_code == 201, r.text
        return r.json()

    return _make


@pytest.fixture
def make_user(client, admin_headers):
    def _make(username="john", balance="10000.00"):
        r = client.post(
            "/api/admin/users/",
            json={"first_name": "John",
                  "last_name": "Smith",
                  "username": username,
                  "birthdate": "1995-05-20",
                  "account_balance": balance},
            headers=admin_headers)
        assert r.status_code == 201, r.text
        return r.json()

    return _make
