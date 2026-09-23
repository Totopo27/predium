from datetime import date, timedelta
from typing import List, Optional
from src.domain.models import EdictoRemate
from src.application.boletin_parser import BoletinJudicialParser
from src.infrastructure.imprenta_client import ImprentaNacionalClient


class CazarRematesService:
    """
    Servicio de aplicación encargado de orquestar la descarga, parseo y filtrado
    de edictos de remate en zonas prioritarias.
    """

    def __init__(
        self,
        client: Optional[ImprentaNacionalClient] = None,
        parser: Optional[BoletinJudicialParser] = None,
    ):
        self.client = client or ImprentaNacionalClient()
        self.parser = parser or BoletinJudicialParser()

    def escanear_fecha(
        self, fecha: date, canton_filtro: Optional[str] = "Zarcero"
    ) -> List[EdictoRemate]:
        """Descarga y extrae los edictos de remate de una fecha específica."""
        # Evitar fines de semana (sábado=5, domingo=6)
        if fecha.weekday() >= 5:
            return []

        html = self.client.descargar_boletin_html(fecha)
        if not html:
            return []

        bloques = self.client.extraer_bloques_remates(html)
        edictos: List[EdictoRemate] = []

        for bloque in bloques:
            if canton_filtro and not self.parser.es_de_canton(bloque, canton_filtro):
                continue

            edicto = self.parser.parsear_texto_edicto(bloque)
            if edicto:
                edicto.fecha_publicacion = fecha
                edictos.append(edicto)

        return edictos

    def escanear_rango(
        self, desde: date, hasta: date, canton_filtro: Optional[str] = "Zarcero"
    ) -> List[EdictoRemate]:
        """Escanea un rango continuo de fechas hábiles."""
        resultados: List[EdictoRemate] = []
        actual = desde
        while actual <= hasta:
            if actual.weekday() < 5:  # Lunes a viernes
                encontrados = self.escanear_fecha(actual, canton_filtro=canton_filtro)
                resultados.extend(encontrados)
            actual += timedelta(days=1)
        return resultados
