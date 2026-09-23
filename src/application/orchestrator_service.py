import time
from datetime import date, datetime, timedelta
from typing import List, Optional
from src.domain.orchestration_models import CicloIngestaLog, AlertaOportunidad
from src.domain.models import EdictoRemate
from src.application.cazar_remates_service import CazarRematesService
from src.application.georreferenciar_service import GeorreferenciarService


class OrchestratorService:
    """
    Orquestador central del pipeline autónomo de buscaCatastro.
    Coordina la descarga diaria, el triage de Sistema 1, la georreferenciación catastral
    y el disparo de alertas de oportunidad de negocio.
    """

    def __init__(
        self,
        cazar_service: Optional[CazarRematesService] = None,
        georreferenciar_service: Optional[GeorreferenciarService] = None,
    ):
        self.cazar_service = cazar_service or CazarRematesService()
        self.georreferenciar_service = georreferenciar_service or GeorreferenciarService()

    def evaluar_alertas(self, edicto: EdictoRemate) -> List[AlertaOportunidad]:
        """Evalúa si un edicto reúne condiciones de oportunidad de alto valor."""
        alertas: List[AlertaOportunidad] = []

        # 1. Morosidad fiscal municipal
        if edicto.es_morosidad_municipal:
            alertas.append(
                AlertaOportunidad(
                    tipo_alerta="MOROSIDAD_MUNICIPAL",
                    folio_real=edicto.finca.folio_real,
                    expediente=edicto.expediente,
                    monto_base=edicto.base.monto_base,
                    moneda=edicto.base.moneda.value,
                    detalles=f"Ejecución por cobro municipal ({edicto.acreedor or 'Municipalidad'}). Posible abandono fiscal y oportunidad de rescate.",
                    prioridad="CRITICA",
                )
            )

        # 2. Tercera subasta (25% de la base)
        if edicto.urgencia == "TERCERA":
            base_tercera = edicto.base.monto_tercer_remate or (edicto.base.monto_base * 0.25)
            alertas.append(
                AlertaOportunidad(
                    tipo_alerta="TERCERA_SUBASTA",
                    folio_real=edicto.finca.folio_real,
                    expediente=edicto.expediente,
                    monto_base=base_tercera,
                    moneda=edicto.base.moneda.value,
                    detalles=f"Propiedad en 3° y última subasta. Base rebajada al 25% ({edicto.base.moneda.value} {base_tercera:,.2f}).",
                    prioridad="ALTA",
                )
            )

        return alertas

    def ejecutar_ciclo_fecha(self, fecha: date, canton: str = "Zarcero") -> CicloIngestaLog:
        """Ejecuta un ciclo completo para una fecha y cantón específicos."""
        t0 = time.perf_counter()

        # Evitar fines de semana
        if fecha.weekday() >= 5:
            return CicloIngestaLog(
                fecha_boletin=fecha,
                canton=canton,
                estado="SIN_NOVEDADES",
                duracion_segundos=0.0,
            )

        try:
            # 1. Escanear con triage de Sistema 1 y deduplicar en BD
            edictos_detectados, nuevos_guardados = self.cazar_service.escanear_fecha(
                fecha=fecha, canton_filtro=canton, guardar=True
            )

            # 2. Georreferenciar fincas nuevas y emitir alertas
            georreferenciados_count = 0
            alertas_ciclo: List[AlertaOportunidad] = []

            for e in edictos_detectados:
                # Disparar alertas de negocio
                alertas_edicto = self.evaluar_alertas(e)
                alertas_ciclo.extend(alertas_edicto)

                # Georreferenciar
                try:
                    geo = self.georreferenciar_service.georreferenciar_edicto(e)
                    if geo.georreferenciado:
                        georreferenciados_count += 1
                except Exception:
                    pass

            duracion = time.perf_counter() - t0

            estado = "EXITOSO" if edictos_detectados else "SIN_NOVEDADES"

            return CicloIngestaLog(
                fecha_boletin=fecha,
                canton=canton,
                total_bloques_analizados=len(edictos_detectados),
                inmuebles_detectados=len(edictos_detectados),
                nuevos_guardados_bd=nuevos_guardados,
                georreferenciados_catastro=georreferenciados_count,
                alertas_emitidas=len(alertas_ciclo),
                alertas=alertas_ciclo,
                duracion_segundos=round(duracion, 2),
                estado=estado,
            )
        except Exception as e:
            duracion = time.perf_counter() - t0
            return CicloIngestaLog(
                fecha_boletin=fecha,
                canton=canton,
                duracion_segundos=round(duracion, 2),
                estado="ERROR",
                mensaje_error=str(e),
            )

    def ejecutar_catchup(
        self, dias_atras: int = 5, canton: str = "Zarcero"
    ) -> List[CicloIngestaLog]:
        """
        Ejecuta un barrido retrospectivo de días hábiles (catch-up) para asegurar
        que no queden publicaciones sin procesar tras fines de semana o cortes de red.
        """
        hoy = date.today()
        logs: List[CicloIngestaLog] = []

        for i in range(dias_atras, -1, -1):
            dia = hoy - timedelta(days=i)
            if dia.weekday() < 5:  # Lunes a viernes
                log = self.ejecutar_ciclo_fecha(fecha=dia, canton=canton)
                logs.append(log)

        return logs
