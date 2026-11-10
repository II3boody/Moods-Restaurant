import os

if os.path.exists("test_moods.db"):  # fresh DB on every run
    os.remove("test_moods.db")
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



def test_bilingual_content():
    with TestClient(app) as c:
        sa = login(c, "superadmin@moods.com", "ChangeMe123!")
        api = "/api/v1"

        # category: English only still works (Arabic nullable), then add Arabic via PATCH
        cat = c.post(f"{api}/categories", headers=sa, json={"name": "Grill"})
        assert cat.status_code == 201 and cat.json()["name_ar"] is None
        cid = cat.json()["id"]
        r = c.patch(f"{api}/categories/{cid}", headers=sa, json={"name_ar": "مشويات", "description_ar": "مشويات طازجة"})
        assert r.json()["name_ar"] == "مشويات" and r.json()["name"] == "Grill"

        # product: both languages on POST, partial PATCH keeps the rest
        p = c.post(f"{api}/products", headers=sa, json={
            "category_id": cid, "name": "Kebab", "name_ar": "كباب", "description": "Grilled",
            "description_ar": "مشوي", "details": "200g", "details_ar": "200 جم", "price": 150})
        assert p.status_code == 201, p.text
        pid = p.json()["id"]
        assert p.json()["details_ar"] == "200 جم"
        r = c.patch(f"{api}/products/{pid}", headers=sa, json={"name_ar": "كباب مشوي"})
        assert r.json()["name_ar"] == "كباب مشوي" and r.json()["details_ar"] == "200 جم"
        assert r.json()["name"] == "Kebab"
        # search works in Arabic too
        assert c.get(f"{api}/products", params={"search": "كباب"}).json()["total"] == 1

        # bundle
        b = c.post(f"{api}/bundles", headers=sa, json={
            "name": "Kebab Deal", "name_ar": "عرض الكباب", "description_ar": "كباب + بطاطس",
            "price": 100, "items": [{"product_id": pid, "quantity": 1}]})
        assert b.status_code == 201, b.text
        assert b.json()["name_ar"] == "عرض الكباب" and b.json()["items"][0]["product"]["name_ar"] == "كباب مشوي"

        # about: Arabic is merged, English is untouched, omitted fields are kept
        before = c.get(f"{api}/about").json()
        assert before["story_ar"] is None or isinstance(before["story_ar"], str)
        r = c.put(f"{api}/about", headers=sa, json={"story_ar": "قصتنا", "mission_ar": "رسالتنا"})
        assert r.status_code == 200 and r.json()["story"] == before["story"]
        r = c.put(f"{api}/about", headers=sa, json={"phone": "0100"})
        assert r.json()["story_ar"] == "قصتنا" and r.json()["phone"] == "0100"

        # home returns the bilingual fields
        home = c.get(f"{api}/home").json()
        assert home["about"]["story_ar"] == "قصتنا" and home["about"]["mission_ar"] == "رسالتنا"
        assert "name_ar" in home["categories"][0]
        assert any(o["name_ar"] == "عرض الكباب" for o in home["offers"])
        if home["popular_products"]:
            assert "name_ar" in home["popular_products"][0]
