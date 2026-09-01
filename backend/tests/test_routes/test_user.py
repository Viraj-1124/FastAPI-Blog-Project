def test_create_user(client):
    data = {"email": "ygyzsx@gmail.com", "password": "Supersecret"}
    response = client.post("/users/",json =data)
    assert response.status_code==201
    assert response.json()["email"] == "ygyzsx@gmail.com"