def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_unknown_route_uses_error_format(client):
    r = client.get("/nope")
    assert r.status_code == 404
    assert r.json() == {"error": "Not Found"}


def test_admin_endpoint_without_key_is_401(client):
    r = client.post("/api/admin/products/", json={"name": "X", "price_per_litre": "1"})
    assert r.status_code == 401
    assert "error" in r.json()


def test_admin_endpoint_with_wrong_key_is_403(client):
    r = client.post(
        "/api/admin/products/",
        json={"name": "X", "price_per_litre": "1"},
        headers={"X-Admin-Key": "wrong"},
    )
    assert r.status_code == 403


def test_regular_user_header_cannot_use_admin_endpoints(client, make_user):
    make_user("john")
    r = client.post(
        "/api/admin/products/",
        json={"name": "X", "price_per_litre": "1"},
        headers={"X-Username": "john"},
    )
    assert r.status_code == 401


def test_create_product(client, admin_headers):
    r = client.post(
        "/api/admin/products/",
        json={"name": "Diesel", "price_per_litre": "450.50", "available_litres": "200"},
        headers=admin_headers,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Diesel"
    assert body["price_per_litre"] == "450.50"
    assert body["available_litres"] == "200.00"


def test_create_product_negative_values_rejected(client, admin_headers):
    for payload in (
        {"name": "A", "price_per_litre": "-1"},
        {"name": "A", "price_per_litre": "1", "available_litres": "-5"},
    ):
        r = client.post("/api/admin/products/", json=payload, headers=admin_headers)
        assert r.status_code == 422
        assert "error" in r.json()


def test_duplicate_product_name_is_409(client, admin_headers, make_product):
    make_product("Diesel")
    r = client.post(
        "/api/admin/products/",
        json={"name": "Diesel", "price_per_litre": "1"},
        headers=admin_headers,
    )
    assert r.status_code == 409


def test_patch_product_price_and_stock(client, admin_headers, make_product):
    p = make_product()
    r = client.patch(
        f"/api/admin/products/{p['id']}/",
        json={"price_per_litre": "520.50", "available_litres": "300"},
        headers=admin_headers,
    )
    assert r.status_code == 200
    assert r.json()["price_per_litre"] == "520.50"
    assert r.json()["available_litres"] == "300.00"
    assert r.json()["name"] == "Petrol 95"


def test_patch_product_errors(client, admin_headers, make_product):
    p = make_product()
    other = make_product("Diesel")
    url = f"/api/admin/products/{p['id']}/"
    assert client.patch("/api/admin/products/9999/", json={"price_per_litre": "1"}, headers=admin_headers).status_code == 404
    assert client.patch(url, json={}, headers=admin_headers).status_code == 422
    assert client.patch(url, json={"price_per_litre": None}, headers=admin_headers).status_code == 422
    assert client.patch(url, json={"price_per_litre": "-1"}, headers=admin_headers).status_code == 422
    assert client.patch(url, json={"name": other["name"]}, headers=admin_headers).status_code == 409


def test_create_user_defaults_balance_to_zero(client, admin_headers):
    r = client.post(
        "/api/admin/users/",
        json={"first_name": "A", "last_name": "B", "username": "ab", "birthdate": "2000-01-01"},
        headers=admin_headers,
    )
    assert r.status_code == 201
    assert r.json()["account_balance"] == "0.00"


def test_duplicate_username_is_409(client, admin_headers, make_user):
    make_user("john")
    r = client.post(
        "/api/admin/users/",
        json={"first_name": "A", "last_name": "B", "username": "john", "birthdate": "2000-01-01"},
        headers=admin_headers,
    )
    assert r.status_code == 409


def test_invalid_user_info_rejected(client, admin_headers):
    base = {"first_name": "A", "last_name": "B", "username": "ab", "birthdate": "2000-01-01"}
    for change in (
        {"birthdate": "2999-01-01"},
        {"birthdate": "not-a-date"},
        {"account_balance": "-5"},
        {"username": "   "},
        {"first_name": ""},
    ):
        r = client.post("/api/admin/users/", json={**base, **change}, headers=admin_headers)
        assert r.status_code == 422, change
        assert "error" in r.json()


def test_patch_user_balance(client, admin_headers, make_user):
    u = make_user("john", "100.00")
    r = client.patch(f"/api/admin/users/{u['id']}/", json={"account_balance": "2500.75"}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["account_balance"] == "2500.75"
    r = client.patch(f"/api/admin/users/{u['id']}/", json={"account_balance": "-1"}, headers=admin_headers)
    assert r.status_code == 422
    assert client.patch("/api/admin/users/9999/", json={"account_balance": "1"}, headers=admin_headers).status_code == 404


def test_patch_user_duplicate_username_is_409(client, admin_headers, make_user):
    make_user("john")
    mary = make_user("mary")
    r = client.patch(f"/api/admin/users/{mary['id']}/", json={"username": "john"}, headers=admin_headers)
    assert r.status_code == 409