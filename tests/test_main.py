from httpx import AsyncClient

async def test_read_main(client: AsyncClient):
    response = await client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "¡Welcome to my API! Visit /docs for the documentation."}