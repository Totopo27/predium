import pytest
from src.infrastructure.laya_triage_client import LayaTriageClient
from src.domain.triage_models import (
    TipoBienClasificado,
    OrigenDeudaClasificado,
    UrgenciaSubasta,
    TipoOportunidadNegocio,
    ViabilidadSaneamiento,
)


def test_triage_abandono_fiscal_score_alto():
    texto = """
    En este Despacho, con la base de quince millones de colones, sáquese a remate la finca del partido de Alajuela, matrícula 245123-000. Se remata en proceso de cobro judicial de Municipalidad de Zarcero contra Contribuyente Moroso por impuestos de bienes inmuebles impagos por 5 años.
    """
    client = LayaTriageClient(usar_modelo_local=False)
    res = client.clasificar_inmueble(texto)

    assert res.es_inmueble is True
    assert res.es_morosidad_municipal is True
    assert res.tipo_oportunidad == TipoOportunidadNegocio.ABANDONO_FISCAL
    assert res.viabilidad_saneamiento == ViabilidadSaneamiento.ALTA
    assert res.score_inversion >= 4


def test_triage_vulnerabilidad_usufructo():
    texto = """
    Finca en San Ramón a nombre de adulto mayor, soportando usufructo vitalicio. Requiere venta de nuda propiedad para costear albergue.
    """
    client = LayaTriageClient(usar_modelo_local=False)
    res = client.clasificar_inmueble(texto)

    assert res.es_inmueble is True
    assert res.tipo_oportunidad == TipoOportunidadNegocio.VULNERABILIDAD_PATRIMONIAL
    assert res.viabilidad_saneamiento == ViabilidadSaneamiento.MEDIA
    assert res.tiene_gravamen_bloqueante is True
    assert "Nuda Propiedad" in str(res.detalles_bloqueo)


def test_triage_liquidacion_bancaria_con_descuento():
    texto = """
    Terreno adjudicado por Banco de Costa Rica BCR en San Ramón BCR-BA1027710922 con 40% de descuento sobre avalúo.
    """
    client = LayaTriageClient(usar_modelo_local=False)
    res = client.clasificar_inmueble(texto, porcentaje_descuento=40.0)

    assert res.es_inmueble is True
    assert res.tipo_oportunidad == TipoOportunidadNegocio.LIQUIDACION_BANCARIA
    assert res.score_inversion >= 4


def test_triage_riesgo_severo_banhvi():
    texto = """
    Inmueble con gravamen de limitación por Bono Familiar de Vivienda (BANHVI Ley 7052) vigente por 10 años.
    """
    client = LayaTriageClient(usar_modelo_local=False)
    res = client.clasificar_inmueble(texto)

    assert res.viabilidad_saneamiento == ViabilidadSaneamiento.BAJA
    assert res.tiene_gravamen_bloqueante is True
    assert res.score_inversion <= 2
