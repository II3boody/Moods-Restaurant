import os

os.environ["DATABASE_URL"] = "sqlite:///./test_moods.db"
os.environ["UPLOAD_DIR"] = "test_uploads"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def login(c, email, password):
    r = c.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_full_flow():
    with TestClient(app) as c:
        # customer
        r = c.post("/api/v1/auth/register", json={
            "full_name": "Ahmed Ali", "email": "ahmed@test.com", "password": "Passw0rd!"})
        assert r.status_code == 201
        user = login(c, "ahmed@test.com", "Passw0rd!")

        # menu + cart + order
        products = c.get("/api/v1/products").json()
        assert products["total"] >= 1
        pid = products["items"][0]["id"]
        cart = c.post("/api/v1/cart/items", json={"product_id": pid, "quantity": 2}, headers=user).json()
        assert cart["items_count"] == 2
        order = c.post("/api/v1/orders", headers=user, json={
            "delivery_address": "Qena, Street 1", "phone": "01000000000"})
        assert order.status_code == 201
        assert c.get("/api/v1/cart", headers=user).json()["items_count"] == 0

        # customer can't use admin endpoints
        assert c.get("/api/v1/admin/stats", headers=user).status_code == 403

        # super admin
        sa = login(c, "superadmin@moods.com", "ChangeMe123!")
        assert c.get("/api/v1/admin/stats", headers=sa).json()["orders"] >= 1
        r = c.patch(f"/api/v1/orders/{order.json()['id']}/status", json={"status": "confirmed"}, headers=sa)
        assert r.status_code == 200
        # invalid transition
        r = c.patch(f"/api/v1/orders/{order.json()['id']}/status", json={"status": "delivered"}, headers=sa)
        assert r.status_code == 400

        # review needs approval
        rv = c.post("/api/v1/reviews", json={"rating": 5, "comment": "great"}, headers=user).json()
        assert c.get("/api/v1/reviews").json()["total"] == 0
        c.patch(f"/api/v1/reviews/{rv['id']}/approve", headers=sa)
        assert c.get("/api/v1/reviews").json()["total"] == 1

        # home aggregated endpoint
        assert "popular_products" in c.get("/api/v1/home").json()

        # offers (bundle): admin creates, customer buys
        b = c.post("/api/v1/bundles", headers=sa, json={
            "name": "Combo", "price": 50,
            "items": [{"product_id": pid, "quantity": 1}, {"product_id": pid, "quantity": 1}]})
        assert b.status_code == 201, b.text
        assert b.json()["items"][0]["quantity"] == 2  # نفس المنتج اتدمج
        assert len(c.get("/api/v1/bundles").json()) >= 1
        cart = c.post("/api/v1/cart/items", json={"bundle_id": b.json()["id"]}, headers=user).json()
        assert cart["items"][0]["bundle"]["name"] == "Combo"
        assert c.post("/api/v1/orders", headers=user, json={
            "delivery_address": "Qena, Street 1", "phone": "01000000000"}).status_code == 201

        # best sellers (محسوبة من الأوردرات) + sub-category
        assert len(c.get("/api/v1/products/best-sellers").json()) >= 1
        parent = c.get("/api/v1/categories").json()[0]["id"]
        sub = c.post("/api/v1/categories", headers=sa, json={"name": "Chicken", "parent_id": parent})
        assert sub.status_code == 201
        assert any(t["children"] for t in c.get("/api/v1/categories/tree").json())

