import httpx
from typing import Optional, List, Dict, Any
from src.domain.gis_models import PredioCatastral
from src.domain.catastro_provider import CatastroProvider


class CatastroZarceroClient(CatastroProvider):
    """
    Proveedor WFS oficial para la Municipalidad de Zarcero (Nivel 1: Alta Resolución).
    """

    BASE_WFS_URL = "https://visorcatastral.zarcero.go.cr/mapas/zarcero/wfs"

    def __init__(self, timeout: float = 20.0):
        self.client = httpx.Client(
            timeout=timeout,
            verify=False,
            headers={
                "User-Agent": "buscaCatastro-Engine/1.0"
            },
        )

    def _ejecutar_wfs_query(
        self, tipo_capa: str, cql_filter: Optional[str] = None, count: int = 50
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

        return PredioCatastral(
            finca=str(props.get("finca", "")).strip(),
            plano=str(props.get("plano", "")).strip() if props.get("plano") else None,
            distrito=str(props.get("n_distrito", "DESCONOCIDO")).strip().upper(),
            area_registro_m2=float(props["a_registro"]) if props.get("a_registro") is not None else None,
            area_poligono_m2=float(props["a_poligono"]) if props.get("a_poligono") is not None else None,
            frente_m=float(props["frente"]) if props.get("frente") is not None else None,
            fondo_m=float(props["fondo"]) if props.get("fondo") is not None else None,
            numero_construcciones=int(props.get("n_construc", 0)),
            categoria=str(props.get("categoria", "Finca Inscrita")),
            centroide_x=float(props.get("x", 0.0)),
            centroide_y=float(props.get("y", 0.0)),
            geometria=geom,
        )

    def buscar_por_finca(self, numero_finca: str) -> Optional[PredioCatastral]:
        finca_limpia = numero_finca.strip().lstrip("0")
        cql = f"finca LIKE '%{finca_limpia}%'"
        try:
            data = self._ejecutar_wfs_query("catastro", cql_filter=cql, count=5)
            features = data.get("features", [])
            if not features:
                return None
            return self._feature_a_predio(features[0])
        except Exception:
            return None

    def buscar_por_plano(self, numero_plano: str) -> Optional[PredioCatastral]:
        plano_limpio = numero_plano.replace("-", "").strip()
        cql = f"plano LIKE '%{plano_limpio}%'"
        try:
            data = self._ejecutar_wfs_query("catastro", cql_filter=cql, count=5)
            features = data.get("features", [])
            if not features:
                return None
            return self._feature_a_predio(features[0])
        except Exception:
            return None

    def obtener_predios_distrito(self, distrito: str, limite: int = 100) -> List[PredioCatastral]:
        distrito_upper = distrito.strip().upper()
        cql = f"n_distrito = '{distrito_upper}'"
        try:
            data = self._ejecutar_wfs_query("catastro", cql_filter=cql, count=limite)
            return [self._feature_a_predio(f) for f in data.get("features", [])]
        except Exception:
            return []
