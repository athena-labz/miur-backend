from fixtures import api


def test_health(api):
    client, _ = api

    response = client.get("/health") 
    
    assert response.status_code == 200
    assert response.json == {"status": True}