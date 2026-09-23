import pytest
from datetime import date
from unittest.mock import MagicMock
from src.domain.models import EdictoRemate, IdentificadorRegistral, UbicacionFinca, BaseRemate, Moneda
from src.domain.gis_models import RemateGeorreferenciado, PredioCatastral
from src.application.orchestrator_service import OrchestratorService
from src.application.cazar_remates_service import CazarRematesService
from src.application.georreferenciar_service import GeorreferenciarService


def test_orquestador_ejecuta_ciclo_y_emite_alertas():
    mock_cazar = MagicMock(spec=CazarRematesService)
    mock_geo = MagicMock(spec=GeorreferenciarService)

    # Simular un edicto de cobro municipal en tercera subasta
    edicto_oro = EdictoRemate(
        id_edicto="IN999",
        fecha_publicacion=date(2024, 5, 10),
        expediente="24-0001-CJ",
        acreedor="Municipalidad de Zarcero",
        finca=IdentificadorRegistral(provincia_codigo=2, numero_finca="555666"),
        ubicacion=UbicacionFinca(provincia="Alajuela", canton="Zarcero", distrito="Guadalupe"),
        base=BaseRemate(moneda=Moneda.CRC, monto_base=12000000.0),
        texto_original="Texto",
        es_morosidad_municipal=True,
        urgencia="TERCERA",
    )

    mock_cazar.escanear_fecha.return_value = ([edicto_oro], 1)
    mock_geo.georreferenciar_edicto.return_value = RemateGeorreferenciado(
        folio_real="2-555666-000",
        base_monto=12000000.0,
        moneda="CRC",
        georreferenciado=True,
    )

    orquestador = OrchestratorService(
        cazar_service=mock_cazar,
        georreferenciar_service=mock_geo,
    )

    log = orquestador.ejecutar_ciclo_fecha(fecha=date(2024, 5, 10), canton="Zarcero")

    assert log.estado == "EXITOSO"
    assert log.nuevos_guardados_bd == 1
    assert log.georreferenciados_catastro == 1
    assert log.alertas_emitidas >= 1

    # Verificar que se emitió la alerta municipal de alta prioridad
    tipos_alertas = [a.tipo_alerta for a in log.alertas]
    assert "MOROSIDAD_MUNICIPAL" in tipos_alertas
    assert "TERCERA_SUBASTA" in tipos_alertas
