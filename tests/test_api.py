from starlette.testclient import TestClient
from src.api.app import app

client = TestClient(app)


def test_api_home():
    response = client.get("/")
    assert response.status_code == 200


def test_api_remates_lista():
    response = client.get("/api/remates?canton=Zarcero")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_api_diagnostico_sociedad_disuelta():
    response = client.get("/api/diagnostico?folio=2-120500-000&escenario=sociedad_disuelta")
    assert response.status_code == 200
    data = response.json()
    assert data["folio_real"] == "2-120500-000"
    assert data["alerta_sociedad_disuelta"] is True
    assert data["estrategia_sugerida"] == "LIQUIDACION_SOCIEDAD_DISUELTA"
