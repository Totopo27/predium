from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.adjudicados_models import BienAdjudicado, InstitucionFinanciera


class BienesAdjudicadosProvider(ABC):
    """Interfaz estándar para conectores de bienes adjudicados de entidades financieras."""

    @property
    @abstractmethod
    def institucion(self) -> InstitucionFinanciera:
        """Institución financiera que provee este adaptador."""
        pass

    @abstractmethod
    def obtener_catalogo(self, canton: Optional[str] = None) -> List[BienAdjudicado]:
        """Extrae el catálogo de bienes adjudicados, opcionalmente filtrando por cantón."""
        pass


class AdjudicadosRepository(ABC):
    """Interfaz para persistencia y consulta de bienes adjudicados."""

    @abstractmethod
    def guardar(self, bien: BienAdjudicado) -> bool:
        pass

    @abstractmethod
    def guardar_muchos(self, bienes: List[BienAdjudicado]) -> int:
        pass

    @abstractmethod
    def listar(
        self,
        canton: Optional[str] = None,
        institucion: Optional[InstitucionFinanciera] = None,
        limite: int = 50,
    ) -> List[BienAdjudicado]:
        pass
