import pytest
from src.infrastructure.laya_triage_client import LayaTriageClient
from src.domain.triage_models import TipoBienClasificado, OrigenDeudaClasificado, UrgenciaSubasta


def test_triage_finca_municipal():
    texto = """
    En este Despacho, con la base de quince millones de colones, sáquese a remate la finca del partido de Alajuela, matrícula 245123-000. Se remata en proceso de cobro judicial de Municipalidad de Zarcero contra Contribuyente Moroso por impuestos de bienes inmuebles.
    """
    client = LayaTriageClient(usar_modelo_local=False)
    res = client.clasificar_edicto(texto)

    assert res.tipo_bien == TipoBienClasificado.INMUEBLE
    assert res.es_inmueble is True
    assert res.origen_deuda == OrigenDeudaClasificado.MUNICIPAL
    assert res.es_morosidad_municipal is True
    assert res.urgencia == UrgenciaSubasta.PRIMERA


def test_triage_vehiculo_para_descarte():
    texto = """
    A las ocho horas del 15 de mayo remataré: vehículo marca Hyundai, estilo Elantra, placas 493857, chasis KMHJF31JPMU, en proceso prendario de Banco X contra Propietario.
    """
    client = LayaTriageClient(usar_modelo_local=False)
    res = client.clasificar_edicto(texto)

    assert res.tipo_bien == TipoBienClasificado.VEHICULO
    assert res.es_inmueble is False


def test_triage_usufructo_y_tercera_subasta():
    texto = """
    Sáquese a remate la finca matrícula 2-998877-000 soportando usufructo vitalicio. Para la tercera subasta se señalan las 10 horas con la base del 25% por ejecución de Banco Nacional.
    """
    client = LayaTriageClient(usar_modelo_local=False)
    res = client.clasificar_edicto(texto)

    assert res.es_inmueble is True
    assert res.riesgo_gravamen_complejo is True
    assert res.probabilidad_riesgo > 0.5
    assert res.urgencia == UrgenciaSubasta.TERCERA
