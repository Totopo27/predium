from typing import Optional
from src.domain.catastro_provider import CatastroProvider
from src.infrastructure.catastro_zarcero_client import CatastroZarceroClient


class CatastroResolver:
    """
    Factory / Resolver que asigna el mejor proveedor catastral disponible
    para un cantón o provincia dada (Patrón Strategy).
    """

    @staticmethod
    def obtener_proveedor(canton: Optional[str] = None) -> CatastroProvider:
        canton_norm = (canton or "").lower().strip()

        # Si el cantón cuenta con nodo municipal optimizado
        if canton_norm in ("zarcero", "alfaro ruiz"):
            return CatastroZarceroClient()

        # Fallback por defecto: en esta versión piloto usamos Zarcero o el cliente nacional
        return CatastroZarceroClient()
