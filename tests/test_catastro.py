import pytest
from unittest.mock import MagicMock
from src.domain.gis_models import PredioCatastral
from src.domain.models import EdictoRemate, IdentificadorRegistral, UbicacionFinca, BaseRemate, Moneda
from src.domain.catastro_provider import CatastroProvider
from src.application.georreferenciar_service import GeorreferenciarService


@pytest.fixture
def predio_mock():
    return PredioCatastral(
        finca="123456",
        plano="A-999-2020",
        distrito="GUADALUPE",
        area_registro_m2=500.0,
        area_poligono_m2=498.5,
        frente_m=12.0,
        fondo_m=41.5,
        numero_construcciones=1,
        categoria="Finca Inscrita",
        centroide_x=450000.0,
        centroide_y=1120000.0,
        geometria={"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]},
    )


def test_georreferenciar_edicto_por_finca(predio_mock):
    mock_client = MagicMock(spec=CatastroProvider)
    mock_client.buscar_por_finca.return_value = predio_mock

    service = GeorreferenciarService(catastro_provider=mock_client)

    edicto = EdictoRemate(
        id_edicto="IN123",
        finca=IdentificadorRegistral(provincia_codigo=2, numero_finca="123456"),
        ubicacion=UbicacionFinca(provincia="Alajuela", canton="Zarcero", distrito="Guadalupe"),
        base=BaseRemate(moneda=Moneda.CRC, monto_base=10000000.0),
        texto_original="Prueba",
    )

    resultado = service.georreferenciar_edicto(edicto)

    assert resultado.georreferenciado is True
    assert resultado.predio is not None
    assert resultado.predio.distrito == "GUADALUPE"
    assert resultado.predio.area_registro_m2 == 500.0
    mock_client.buscar_por_finca.assert_called_once_with("123456")


def test_georreferenciar_edicto_por_plano_fallback(predio_mock):
    mock_client = MagicMock(spec=CatastroProvider)
    mock_client.buscar_por_finca.return_value = None
    mock_client.buscar_por_plano.return_value = predio_mock

    service = GeorreferenciarService(catastro_provider=mock_client)

    edicto = EdictoRemate(
        id_edicto="IN456",
        finca=IdentificadorRegistral(provincia_codigo=2, numero_finca="000000", plano_catastrado="A-999-2020"),
        ubicacion=UbicacionFinca(provincia="Alajuela", canton="Zarcero", distrito="Guadalupe"),
        base=BaseRemate(moneda=Moneda.CRC, monto_base=10000000.0),
        texto_original="Prueba",
    )

    resultado = service.georreferenciar_edicto(edicto)

    assert resultado.georreferenciado is True
    assert resultado.predio is not None
    mock_client.buscar_por_plano.assert_called_once_with("A-999-2020")
