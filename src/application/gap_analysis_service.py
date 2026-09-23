import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from shapely.geometry import shape, MultiPolygon, Polygon
from shapely.ops import unary_union
from src.domain.gap_models import ResultadoGapAnalysis, VacioCatastral
from src.application.gap_detector import GapDetector
from src.infrastructure.catastro_zarcero_client import CatastroZarceroClient


class GapAnalysisService:
    """
    Servicio de orquestación para ejecutar el análisis de vacíos territoriales
    usando los servicios WFS oficiales y exportar los resultados a GeoJSON.
    """

    def __init__(
        self,
        catastro_client: Optional[CatastroZarceroClient] = None,
        detector: Optional[GapDetector] = None,
    ):
        self.catastro_client = catastro_client or CatastroZarceroClient()
        self.detector = detector or GapDetector()

    def ejecutar_analisis_distrito(
        self, distrito: str, area_minima_m2: float = 300.0, area_maxima_m2: float = 80000.0, limite_predios: int = 150
    ) -> Optional[ResultadoGapAnalysis]:
        """
        Ejecuta el análisis de vacíos topológicos para un distrito de Zarcero.
        Utiliza el envolvente (Convex Hull) de los predios si no hay capa distrital separada.
        Descarta polígonos que superen el área máxima de lote para evitar el perímetro rural exterior.
        """
        predios_modelos = self.catastro_client.obtener_predios_distrito(distrito, limite=limite_predios)
        if not predios_modelos:
            return None

        predios_input = [
            {"finca": p.finca, "geometry": p.geometria} for p in predios_modelos
        ]

        # Construir la envolvente territorial a partir de los predios analizados
        geoms = [shape(p["geometry"]) for p in predios_input if shape(p["geometry"]).is_valid]
        if not geoms:
            return None

        # Convex Hull que define la zona geográfica de influencia de este grupo de predios
        envolvente_zona = unary_union(geoms).convex_hull

        resultado = self.detector.analizar_zona(
            distrito_nombre=distrito,
            geometria_distrito=envolvente_zona,
            predios_catastrados=predios_input,
            area_minima_m2=area_minima_m2,
            area_maxima_m2=area_maxima_m2,
        )

        return resultado

    @staticmethod
    def exportar_vacios_geojson(
        resultado: ResultadoGapAnalysis, ruta_salida: str
    ) -> str:
        path = Path(ruta_salida)
        path.parent.mkdir(parents=True, exist_ok=True)

        features = []
        for v in resultado.vacios:
            props = {
                "id_vacio": v.id_vacio,
                "distrito": v.distrito,
                "area_estimada_m2": v.area_estimada_m2,
                "perimetro_m": v.perimetro_m,
                "centroide_x": v.centroide_x,
                "centroide_y": v.centroide_y,
                "fincas_colindantes": ", ".join(v.fincas_colindantes),
                "tipo_hallazgo": "Posible Bien Vacante / Finca No Registrada",
            }
            feat = {
                "type": "Feature",
                "properties": props,
                "geometry": v.geometria,
            }
            features.append(feat)

        geojson_data = {
            "type": "FeatureCollection",
            "crs": {
                "type": "name",
                "properties": {"name": "urn:ogc:def:crs:EPSG::5367"},
            },
            "features": features,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(geojson_data, f, indent=2, ensure_ascii=False)

        return str(path)
