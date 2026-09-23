import pytest
from src.domain.registro_models import (
    TitularFinca,
    TipoPersona,
    Gravamen,
    GravamenTipo,
    EstadoSociedad,
    EstrategiaSaneamiento,
)
from src.application.diagnostico_patrimonial_service import DiagnosticoPatrimonialService


def test_diagnostico_sociedad_disuelta():
    service = DiagnosticoPatrimonialService()

    titulares = [
        TitularFinca(
            nombre="Inversiones El Roble S.A.",
            cedula="3-101-123456",
            tipo=TipoPersona.JURIDICA,
        )
    ]
    gravamenes = []

    diag = service.evaluar_finca(
        folio_real="2-120500-000",
        titulares=titulares,
        gravamenes=gravamenes,
        estado_sociedad=EstadoSociedad.DISUELTA_POR_LEY_9428,
    )

    assert diag.alerta_sociedad_disuelta is True
    assert diag.estrategia_sugerida == EstrategiaSaneamiento.LIQUIDACION_SOCIEDAD_DISUELTA
    assert "extinguida" in diag.diagnostico_resumen.lower() or "disuelta" in diag.diagnostico_resumen.lower()


def test_diagnostico_compra_previa_remate_por_embargo():
    service = DiagnosticoPatrimonialService()

    titulares = [
        TitularFinca(
            nombre="Carlos Gomez",
            cedula="1-0987-0654",
            tipo=TipoPersona.FISICA,
        )
    ]
    gravamenes = [
        Gravamen(
            tipo=GravamenTipo.EMBARGO,
            descripcion="Embargo decretado por Juzgado de Cobro de Alajuela",
            acreedor_o_beneficiario="Banco Nacional",
            monto=18000000.0,
        ),
        Gravamen(
            tipo=GravamenTipo.HIPOTECA,
            descripcion="Hipoteca de primer grado",
            acreedor_o_beneficiario="Cooperativa X",
            monto=25000000.0,
        ),
    ]

    diag = service.evaluar_finca(
        folio_real="2-334455-000",
        titulares=titulares,
        gravamenes=gravamenes,
    )

    assert diag.alerta_embargos_judiciales is True
    assert diag.alerta_hipotecas_activas is True
    assert diag.estrategia_sugerida == EstrategiaSaneamiento.COMPRA_PREVIA_REMATE


def test_diagnostico_nuda_propiedad_usufructo():
    service = DiagnosticoPatrimonialService()

    titulares = [
        TitularFinca(
            nombre="Maria Rodriguez (Adulto Mayor)",
            cedula="2-0123-0456",
            tipo=TipoPersona.FISICA,
        )
    ]
    gravamenes = [
        Gravamen(
            tipo=GravamenTipo.USUFRUCTO,
            descripcion="Usufructo vitalicio a favor de Maria Rodriguez",
        )
    ]

    diag = service.evaluar_finca(
        folio_real="2-556677-000",
        titulares=titulares,
        gravamenes=gravamenes,
    )

    assert diag.alerta_usufructo_activo is True
    assert diag.estrategia_sugerida == EstrategiaSaneamiento.NUDA_PROPIEDAD_USUFRUCTO
