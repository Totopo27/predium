import logging
from typing import Optional, List
from src.domain.gis_models import PredioCatastral
from src.domain.catastro_provider import CatastroProvider

logger = logging.getLogger(__name__)


class FallbackCatastroProvider(CatastroProvider):
    """
    Proveedor catastral de contingencia para cantones sin servidor WFS municipal propio abierto.
    Evita consultar municipios incorrectos por error y mantiene un contrato seguro.
    """

    def __init__(self, canton_nombre: str = "Desconocido"):
        self.canton_nombre = canton_nombre

    def buscar_por_finca(self, numero_finca: str) -> Optional[PredioCatastral]:
        logger.info(
            f"[CATASTRO-FALLBACK] Cantón '{self.canton_nombre}' sin WFS municipal directo. "
            f"Finca {numero_finca} requiere consulta al visor central del SNIT."
        )
        return None

    def buscar_por_plano(self, numero_plano: str) -> Optional[PredioCatastral]:
        logger.info(
            f"[CATASTRO-FALLBACK] Cantón '{self.canton_nombre}' sin WFS municipal directo. "
            f"Plano {numero_plano} requiere consulta al visor central del SNIT."
        )
        return None

    def obtener_predios_distrito(self, distrito: str, limite: int = 100) -> List[PredioCatastral]:
        logger.info(
            f"[CATASTRO-FALLBACK] Cantón '{self.canton_nombre}' sin capa predial municipal abierta para distrito '{distrito}'."
        )
        return []
