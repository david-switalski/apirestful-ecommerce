from fastapi.testclient import TestClient

async def test_read_main(client: TestClient):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "¡Welcome to my API! Visit /docs for the documentation."}