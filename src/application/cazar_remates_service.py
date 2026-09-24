from datetime import date, timedelta
from typing import List, Optional
from src.domain.models import EdictoRemate
from src.domain.repository_interface import RemateRepository
from src.application.boletin_parser import BoletinJudicialParser
from src.infrastructure.imprenta_client import ImprentaNacionalClient
from src.infrastructure.sqlite_repository import SqliteRemateRepository
from src.infrastructure.laya_triage_client import LayaTriageClient


class CazarRematesService:
    """
    Servicio de aplicación encargado de orquestar la descarga, parseo, filtrado,
    triage multidimensional de Sistema 1 y persistencia con deduplicación de edictos de remate.
    """

    def __init__(
        self,
        client: Optional[ImprentaNacionalClient] = None,
        parser: Optional[BoletinJudicialParser] = None,
        repository: Optional[RemateRepository] = None,
        triage_client: Optional[LayaTriageClient] = None,
    ):
        self.client = client or ImprentaNacionalClient()
        self.parser = parser or BoletinJudicialParser()
        self.repository = repository or SqliteRemateRepository()
        self.triage_client = triage_client or LayaTriageClient()

    def escanear_fecha(
        self, fecha: date, canton_filtro: Optional[str] = "Zarcero", guardar: bool = True
    ) -> tuple[List[EdictoRemate], int]:
        """
        Descarga y extrae los edictos de remate de una fecha específica.
        Aplica filtro geográfico y triage de Sistema 1 en 5 dimensiones.
        Retorna (lista_detectados, cantidad_nuevos_guardados).
        """
        if fecha.weekday() >= 5:
            return [], 0

        html = self.client.descargar_boletin_html(fecha)
        if not html:
            return [], 0

        bloques = self.client.extraer_bloques_remates(html)
        edictos: List[EdictoRemate] = []

        for bloque in bloques:
            if canton_filtro and not self.parser.es_de_canton(bloque, canton_filtro):
                continue

            # Triage holístico con Laya (Sistema 1)
            triage = self.triage_client.clasificar_inmueble(bloque)
            if not triage.es_inmueble:
                # Descartar vehículos o bienes muebles
                continue

            edicto = self.parser.parsear_texto_edicto(bloque)
            if edicto:
                edicto.fecha_publicacion = fecha
                edicto.tipo_bien = triage.tipo_bien.value
                edicto.origen_deuda = triage.origen_deuda.value
                edicto.es_morosidad_municipal = triage.es_morosidad_municipal
                edicto.tipo_oportunidad = triage.tipo_oportunidad.value
                edicto.viabilidad_saneamiento = triage.viabilidad_saneamiento.value
                edicto.tiene_gravamen_bloqueante = triage.tiene_gravamen_bloqueante
                edicto.detalles_bloqueo = triage.detalles_bloqueo
                edicto.urgencia = triage.urgencia.value
                edicto.score_inversion = triage.score_inversion
                edictos.append(edicto)

        nuevos = 0
        if guardar and edictos:
            nuevos = self.repository.guardar_muchos(edictos)

        return edictos, nuevos

    def escanear_rango(
        self, desde: date, hasta: date, canton_filtro: Optional[str] = "Zarcero", guardar: bool = True
    ) -> tuple[List[EdictoRemate], int]:
        """Escanea un rango continuo de fechas hábiles."""
        total_edictos: List[EdictoRemate] = []
        total_nuevos = 0
        actual = desde

        while actual <= hasta:
            if actual.weekday() < 5:
                encontrados, nuevos = self.escanear_fecha(
                    actual, canton_filtro=canton_filtro, guardar=guardar
                )
                total_edictos.extend(encontrados)
                total_nuevos += nuevos
            actual += timedelta(days=1)

        return total_edictos, total_nuevos
