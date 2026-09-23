from typing import List, Optional
from src.domain.registro_models import (
    DiagnosticoJuridicoFinca,
    TitularFinca,
    Gravamen,
    GravamenTipo,
    EstadoSociedad,
    EstrategiaSaneamiento,
    TipoPersona,
)


class DiagnosticoPatrimonialService:
    """
    Motor de análisis legal e inmobiliario sobre el estado registral de un bien inmueble.
    Determina la viabilidad de saneamiento, rescate previo a remate o compra de nuda propiedad.
    """

    def evaluar_finca(
        self,
        folio_real: str,
        titulares: List[TitularFinca],
        gravamenes: List[Gravamen],
        estado_sociedad: EstadoSociedad = EstadoSociedad.NO_APLICA,
    ) -> DiagnosticoJuridicoFinca:
        tiene_sociedad_disuelta = False
        if estado_sociedad == EstadoSociedad.DISUELTA_POR_LEY_9428:
            tiene_sociedad_disuelta = True
        else:
            for t in titulares:
                if t.tipo == TipoPersona.JURIDICA and estado_sociedad in (
                    EstadoSociedad.DISUELTA_POR_LEY_9428,
                    EstadoSociedad.EN_LIQUIDACION,
                ):
                    tiene_sociedad_disuelta = True
                    break

        tipos_gravamen = [g.tipo for g in gravamenes if not g.cancelado]

        tiene_embargo = GravamenTipo.EMBARGO in tipos_gravamen or GravamenTipo.DEMANDA in tipos_gravamen
        tiene_hipoteca = GravamenTipo.HIPOTECA in tipos_gravamen
        tiene_usufructo = GravamenTipo.USUFRUCTO in tipos_gravamen

        # Determinación de la estrategia de negocio y saneamiento
        if tiene_sociedad_disuelta:
            estrategia = EstrategiaSaneamiento.LIQUIDACION_SOCIEDAD_DISUELTA
            resumen = (
                "Propiedad en limbo legal a nombre de sociedad mercantil extinguida por Ley 9428. "
                "Oportunidad de adquisición por debajo de valor de mercado mediante proceso notarial/judicial "
                "de nombramiento de liquidador según el Código de Comercio."
            )
        elif tiene_embargo or (tiene_hipoteca and len(gravamenes) >= 2):
            estrategia = EstrategiaSaneamiento.COMPRA_PREVIA_REMATE
            resumen = (
                "Alto riesgo de remate por ejecución judicial o hipotecaria. "
                "Intervención estratégica antes de la subasta municipal/bancaria para cancelar o novar el pasivo "
                "y transferir el inmueble saneado con descuento de oportunidad."
            )
        elif tiene_usufructo:
            estrategia = EstrategiaSaneamiento.NUDA_PROPIEDAD_USUFRUCTO
            resumen = (
                "Inmueble con usufructo vitalicio constituido. "
                "Oportunidad de adquisición de nuda propiedad respetando el derecho habitacional/vitalicio "
                "del titular a cambio de renta periódica o cobertura de cuidados/albergue."
            )
        elif tiene_hipoteca:
            estrategia = EstrategiaSaneamiento.LIMPIEZA_GRAVAMENES_PRESCRITOS
            resumen = (
                "Finca con hipoteca registrada. Verificar antigüedad para eventual aplicación de prescripción "
                "decretada según el Código Civil o cancelación voluntaria por bajo saldo."
            )
        else:
            estrategia = EstrategiaSaneamiento.REGULAR
            resumen = "Inmueble sin gravámenes complejos aparentes. Título expedito para negociación ordinaria."

        return DiagnosticoJuridicoFinca(
            folio_real=folio_real,
            titulares=titulares,
            gravamenes=gravamenes,
            estado_sociedad=estado_sociedad,
            alerta_sociedad_disuelta=tiene_sociedad_disuelta,
            alerta_usufructo_activo=tiene_usufructo,
            alerta_embargos_judiciales=tiene_embargo,
            alerta_hipotecas_activas=tiene_hipoteca,
            estrategia_sugerida=estrategia,
            diagnostico_resumen=resumen,
        )
