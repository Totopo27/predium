from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.gis_models import PredioCatastral


class CatastroProvider(ABC):
    """Interfaz universal para cualquier proveedor de datos catastrales en Costa Rica."""

    @abstractmethod
    def buscar_por_finca(self, numero_finca: str) -> Optional[PredioCatastral]:
        """Busca un predio por número de finca."""
        pass

    @abstractmethod
    def buscar_por_plano(self, numero_plano: str) -> Optional[PredioCatastral]:
        """Busca un predio por número de plano catastrado."""
        pass

    @abstractmethod
    def obtener_predios_distrito(self, distrito: str, limite: int = 100) -> List[PredioCatastral]:
        """Obtiene predios por distrito."""
        pass
