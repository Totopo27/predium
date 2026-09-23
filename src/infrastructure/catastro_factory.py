from typing import Optional
from src.domain.catastro_provider import CatastroProvider
from src.infrastructure.catastro_zarcero_client import CatastroZarceroClient
from src.infrastructure.catastro_san_ramon_client import CatastroSanRamonClient


class CatastroResolver:
    """
    Factory / Resolver que asigna el mejor proveedor catastral disponible
    para un cantón o provincia dada (Patrón Strategy).
    """

    @staticmethod
    def obtener_proveedor(canton: Optional[str] = None) -> CatastroProvider:
        canton_norm = (canton or "").lower().strip()

        # Si es San Ramón
        if "ramon" in canton_norm or "ramón" in canton_norm:
            return CatastroSanRamonClient()

        # Si es Zarcero o default
        if canton_norm in ("zarcero", "alfaro ruiz"):
            return CatastroZarceroClient()

        # Fallback general
        return CatastroZarceroClient()
