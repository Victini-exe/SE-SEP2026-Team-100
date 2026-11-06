def test_register_and_login_success(client):
    payload = {"name": "Student One", "institute_email": "student1@study.iitm.ac.in", "password": "password123", "role": "student"}
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201, res.text
    login = client.post("/api/v1/auth/login", json={"institute_email": payload["institute_email"], "password": payload["password"]})
    assert login.status_code == 200, login.text
    assert "access_token" in login.json()


def test_invalid_login_credentials(client):
    response = client.post("/api/v1/auth/login", json={"institute_email": "missing@example.com", "password": "wrong"})
    assert response.status_code == 401


def test_unauthorized_access_to_admin(client):
    response = client.get("/api/v1/admin/dashboard")
    assert response.status_code == 401


def test_registration_rejects_disallowed_domain(client):
    response = client.post("/api/v1/auth/register", json={"name": "Bad", "institute_email": "bad@gmail.com", "password": "password123", "role": "student"})
    assert response.status_code == 400
