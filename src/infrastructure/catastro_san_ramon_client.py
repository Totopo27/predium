import httpx
import re
from typing import Optional, List, Dict, Any
from src.domain.gis_models import PredioCatastral
from src.domain.catastro_provider import CatastroProvider

# Mapeo de distritos de San Ramón (Cantón 02 de Alajuela) al código de identificación predial
DISTRITOS_SAN_RAMON_CODIGOS: Dict[str, str] = {
    "SAN RAMON": "20201",
    "SAN RAMÓN": "20201",
    "SANTIAGO": "20202",
    "SAN JUAN": "20203",
    "PIEDADES NORTE": "20204",
    "PIEDADES SUR": "20205",
    "SAN RAFAEL": "20206",
    "SAN ISIDRO": "20207",
    "ANGELES": "20208",
    "ÁNGELES": "20208",
    "ALFARO": "20209",
    "VOLIO": "20210",
    "CONCEPCION": "20211",
    "CONCEPCIÓN": "20211",
    "ZAPOTAL": "20212",
    "PENAS BLANCAS": "20213",
    "PEÑAS BLANCAS": "20213",
    "SAN LORENZO": "20214",
}


def sanitizar_cql_param(valor: str) -> str:
    return re.sub(r"['\";\\]", "", valor).strip()


class CatastroSanRamonClient(CatastroProvider):
    """
    Proveedor WFS oficial para la Municipalidad de San Ramón (Cantón 02 de Alajuela).
    Consume directamente la capa catastral municipal 'mapa_catastral_municipal'.
    """

    BASE_WFS_URL = "https://visor.sanramon.go.cr/mapas/sanramon/wfs"

    def __init__(self, timeout: float = 20.0):
        self.client = httpx.Client(
            timeout=timeout,
            verify=False,
            headers={
                "User-Agent": "buscaCatastro-Engine/1.0"
            },
        )

    def _ejecutar_wfs_query(
        self, tipo_capa: str = "mapa_catastral_municipal", cql_filter: Optional[str] = None, count: int = 50
    ) -> Dict[str, Any]:
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeNames": tipo_capa,
            "outputFormat": "application/json",
            "count": count,
        }
        if cql_filter:
            params["cql_filter"] = cql_filter

        response = self.client.get(self.BASE_WFS_URL, params=params)
        response.raise_for_status()
        return response.json()

    def _feature_a_predio(self, feat: Dict[str, Any]) -> PredioCatastral:
        props = feat.get("properties", {})
        geom = feat.get("geometry", {})

        # Extraer distrito a partir del código identifica (ej: 20201 -> San Ramón)
        identifica = str(props.get("identifica") or props.get("bloque") or "")
        distrito_nombre = "SAN RAMON"
        for d_nom, d_cod in DISTRITOS_SAN_RAMON_CODIGOS.items():
            if identifica.startswith(d_cod):
                distrito_nombre = d_nom
                break

        # Calcular centroide aproximado si no viene explícito
        coords = geom.get("coordinates", [])
        cx, cy = 450000.0, 1115000.0  # Rango aproximado San Ramón CRTM05
        if coords:
            try:
                def extraer_primer_punto(c: Any) -> Any:
                    if isinstance(c[0], (int, float)):
                        return c[0], c[1]
                    return extraer_primer_punto(c[0])
                cx, cy = extraer_primer_punto(coords)
            except Exception:
                pass

        return PredioCatastral(
            finca=str(props.get("finca", "")).strip(),
            plano=str(props.get("plano", "")).strip() if props.get("plano") else None,
            distrito=distrito_nombre,
            area_registro_m2=float(props["shape_area"]) if props.get("shape_area") is not None else None,
            area_poligono_m2=float(props["shape_area"]) if props.get("shape_area") is not None else None,
            frente_m=None,
            fondo_m=None,
            numero_construcciones=0,
            categoria="Finca Inscrita",
            centroide_x=float(cx),
            centroide_y=float(cy),
            geometria=geom,
        )

    def buscar_por_finca(self, numero_finca: str) -> Optional[PredioCatastral]:
        finca_limpia = sanitizar_cql_param(numero_finca.lstrip("0"))
        if not finca_limpia:
            return None
        cql = f"finca LIKE '%{finca_limpia}%'"
        try:
            data = self._ejecutar_wfs_query(cql_filter=cql, count=5)
            features = data.get("features", [])
            if not features:
                return None
            return self._feature_a_predio(features[0])
        except Exception:
            return None

    def buscar_por_plano(self, numero_plano: str) -> Optional[PredioCatastral]:
        plano_limpio = sanitizar_cql_param(numero_plano.replace("-", ""))
        if not plano_limpio:
            return None
        cql = f"plano LIKE '%{plano_limpio}%'"
        try:
            data = self._ejecutar_wfs_query(cql_filter=cql, count=5)
            features = data.get("features", [])
            if not features:
                return None
            return self._feature_a_predio(features[0])
        except Exception:
            return None

    def obtener_predios_distrito(self, distrito: str, limite: int = 100) -> List[PredioCatastral]:
        distrito_upper = sanitizar_cql_param(distrito.upper())
        cod_prefix = DISTRITOS_SAN_RAMON_CODIGOS.get(distrito_upper, "20201")
        cql = f"identifica LIKE '{cod_prefix}%' OR bloque LIKE '{cod_prefix}%'"
        try:
            data = self._ejecutar_wfs_query(cql_filter=cql, count=limite)
            return [self._feature_a_predio(f) for f in data.get("features", [])]
        except Exception:
            return []
