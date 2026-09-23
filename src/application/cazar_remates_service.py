from datetime import date, timedelta
from typing import List, Optional
from src.domain.models import EdictoRemate
from src.domain.repository_interface import RemateRepository
from src.application.boletin_parser import BoletinJudicialParser
from src.infrastructure.imprenta_client import ImprentaNacionalClient
from src.infrastructure.sqlite_repository import SqliteRemateRepository


class CazarRematesService:
    """
    Servicio de aplicación encargado de orquestar la descarga, parseo, filtrado
    y persistencia con deduplicación de edictos de remate.
    """

    def __init__(
        self,
        client: Optional[ImprentaNacionalClient] = None,
        parser: Optional[BoletinJudicialParser] = None,
        repository: Optional[RemateRepository] = None,
    ):
        self.client = client or ImprentaNacionalClient()
        self.parser = parser or BoletinJudicialParser()
        self.repository = repository or SqliteRemateRepository()

    def escanear_fecha(
        self, fecha: date, canton_filtro: Optional[str] = "Zarcero", guardar: bool = True
    ) -> tuple[List[EdictoRemate], int]:
        """
        Descarga y extrae los edictos de remate de una fecha específica.
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

            edicto = self.parser.parsear_texto_edicto(bloque)
            if edicto:
                edicto.fecha_publicacion = fecha
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
