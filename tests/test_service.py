from datetime import date
from unittest.mock import MagicMock
from src.application.cazar_remates_service import CazarRematesService
from src.infrastructure.imprenta_client import ImprentaNacionalClient


def test_cazar_remates_service_filtra_zarcero():
    mock_client = MagicMock(spec=ImprentaNacionalClient)
    mock_client.descargar_boletin_html.return_value = "<html>dummy</html>"
    mock_client.extraer_bloques_remates.return_value = [
        "En este Despacho, sáquese a remate finca del partido de Alajuela, matrícula número 111111-000, situada en cantón Zarcero. Plano A-123. Expediente 23-1111-CJ. Base: diez millones. ( IN2024111111 ).",
        "En este Despacho, sáquese a remate finca del partido de San José, matrícula número 222222-000, situada en cantón Escazú. Base: veinte millones. ( IN2024222222 ).",
    ]

    service = CazarRematesService(client=mock_client)
    # Lunes 21 de agosto de 2023
    fecha = date(2023, 8, 21)
    
    resultados = service.escanear_fecha(fecha, canton_filtro="Zarcero")

    assert len(resultados) == 1
    assert resultados[0].finca.numero_finca == "111111"
    assert resultados[0].finca.folio_real == "2-111111-000"
    assert "Zarcero" in resultados[0].ubicacion.canton
