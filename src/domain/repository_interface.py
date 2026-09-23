from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.models import EdictoRemate


class RemateRepository(ABC):
    """Interfaz abstracta para la persistencia de edictos de remate."""

    @abstractmethod
    def guardar(self, edicto: EdictoRemate) -> bool:
        """Guarda o actualiza un edicto. Retorna True si fue insertado, False si ya existía."""
        pass

    @abstractmethod
    def guardar_muchos(self, edictos: List[EdictoRemate]) -> int:
        """Guarda una lista de edictos y retorna la cantidad de registros nuevos."""
        pass

    @abstractmethod
    def listar(
        self,
        canton: Optional[str] = None,
        estado: Optional[str] = None,
        limite: int = 50,
    ) -> List[EdictoRemate]:
        """Obtiene la lista de remates almacenados con filtros opcionales."""
        pass

    @abstractmethod
    def obtener_por_folio_real(self, folio_real: str) -> Optional[EdictoRemate]:
        """Busca un remate por su Folio Real único."""
        pass
