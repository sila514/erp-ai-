def test_register_and_login(client):
    resp = client.post(
        "/api/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "s3cret123", "role": "admin"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["username"] == "alice"
    assert body["role"] == "admin"

    resp = client.post("/api/auth/login", data={"username": "alice", "password": "s3cret123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_register_duplicate_username_rejected(client):
    payload = {"username": "bob", "email": "bob@example.com", "password": "pw123456", "role": "sales"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 400


def test_login_wrong_password_rejected(client):
    client.post(
        "/api/auth/register",
        json={"username": "carol", "email": "carol@example.com", "password": "correct-pw", "role": "sales"},
    )
    resp = client.post("/api/auth/login", data={"username": "carol", "password": "wrong-pw"})
    assert resp.status_code == 401


def test_me_requires_valid_token(client, db):
    from tests.conftest import auth_headers

    headers = auth_headers(client, "dave", "pw123456")
    resp = client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "dave"

    resp = client.get("/api/auth/me")
    assert resp.status_code == 401
