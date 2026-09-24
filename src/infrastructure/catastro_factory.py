from typing import Optional, List, Dict
from src.domain.catastro_provider import CatastroProvider
from src.domain.territorio_models import TerritorioInfo, DistritoInfo
from src.infrastructure.catastro_zarcero_client import CatastroZarceroClient
from src.infrastructure.catastro_san_ramon_client import CatastroSanRamonClient
from src.infrastructure.catastro_fallback_client import FallbackCatastroProvider


TERRITORIOS_SOPORTADOS: Dict[str, TerritorioInfo] = {
    "Zarcero": TerritorioInfo(
        canton="Zarcero",
        provincia="Alajuela",
        codigo_canton="11",
        centro_lng_lat=[-84.394, 10.188],
        proveedor_activo=True,
        descripcion_cobertura="WFS Municipal 2.0.0 (visorcatastral.zarcero.go.cr)",
        distritos=[
            DistritoInfo(id="TODOS", label="Todo el Cantón (7 Distritos)"),
            DistritoInfo(id="GUADALUPE", label="Guadalupe"),
            DistritoInfo(id="ZAPOTE", label="Zapote"),
            DistritoInfo(id="PALMIRA", label="Palmira"),
            DistritoInfo(id="ZARCERO", label="Zarcero Centro"),
            DistritoInfo(id="LAGUNA", label="Laguna"),
            DistritoInfo(id="TAPESCO", label="Tapesco"),
            DistritoInfo(id="BRISAS", label="Brisas"),
        ],
    ),
    "San Ramón": TerritorioInfo(
        canton="San Ramón",
        provincia="Alajuela",
        codigo_canton="02",
        centro_lng_lat=[-84.470, 10.088],
        proveedor_activo=True,
        descripcion_cobertura="WFS Municipal 2.0.0 (visor.sanramon.go.cr)",
        distritos=[
            DistritoInfo(id="TODOS", label="Todo el Cantón (14 Distritos)"),
            DistritoInfo(id="SAN RAMON", label="San Ramón Centro"),
            DistritoInfo(id="CONCEPCION", label="Concepción"),
            DistritoInfo(id="SANTIAGO", label="Santiago"),
            DistritoInfo(id="SAN JUAN", label="San Juan"),
            DistritoInfo(id="PIEDADES NORTE", label="Piedades Norte"),
            DistritoInfo(id="PIEDADES SUR", label="Piedades Sur"),
            DistritoInfo(id="SAN RAFAEL", label="San Rafael"),
            DistritoInfo(id="SAN ISIDRO", label="San Isidro"),
            DistritoInfo(id="ANGELES", label="Ángeles"),
            DistritoInfo(id="ALFARO", label="Alfaro"),
            DistritoInfo(id="VOLIO", label="Volio"),
            DistritoInfo(id="ZAPOTAL", label="Zapotal"),
            DistritoInfo(id="PENAS BLANCAS", label="Peñas Blancas"),
            DistritoInfo(id="SAN LORENZO", label="San Lorenzo"),
        ],
    ),
}


class CatastroResolver:
    """
    Factory / Resolver que asigna el mejor proveedor catastral disponible
    para un cantón o provincia dada (Patrón Strategy).
    Garantiza que cantones sin proveedor caigan en Fallback controlado en vez de cruzar datos erróneos.
    """

    @staticmethod
    def listar_territorios() -> List[TerritorioInfo]:
        """Devuelve el catálogo oficial de territorios soportados y sus metadatos."""
        return list(TERRITORIOS_SOPORTADOS.values())

    @staticmethod
    def obtener_proveedor(canton: Optional[str] = None) -> CatastroProvider:
        canton_norm = (canton or "").lower().strip()

        # San Ramón
        if "ramon" in canton_norm or "ramón" in canton_norm:
            return CatastroSanRamonClient()

        # Zarcero / Alfaro Ruiz
        if canton_norm in ("zarcero", "alfaro ruiz"):
            return CatastroZarceroClient()

        # Fallback seguro para cantones sin WFS municipal propio
        canton_label = canton.strip().title() if canton else "Desconocido"
        return FallbackCatastroProvider(canton_nombre=canton_label)
