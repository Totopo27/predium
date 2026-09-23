import json
from typing import List, Optional, Dict, Any
from pathlib import Path
from src.domain.models import EdictoRemate
from src.domain.gis_models import PredioCatastral, RemateGeorreferenciado
from src.domain.catastro_provider import CatastroProvider
from src.domain.repository_interface import RemateRepository
from src.infrastructure.catastro_factory import CatastroResolver
from src.infrastructure.sqlite_repository import SqliteRemateRepository


class GeorreferenciarService:
    """
    Servicio de aplicación para cruzar los edictos de remate con la cartografía
    oficial del catastro y generar capas espaciales enriquecidas.
    """

    def __init__(
        self,
        catastro_provider: Optional[CatastroProvider] = None,
        repository: Optional[RemateRepository] = None,
    ):
        self.catastro_provider = catastro_provider
        self.repository = repository or SqliteRemateRepository()

    def _resolver_proveedor(self, canton: Optional[str]) -> CatastroProvider:
        if self.catastro_provider:
            return self.catastro_provider
        return CatastroResolver.obtener_proveedor(canton)

    def georreferenciar_edicto(self, edicto: EdictoRemate) -> RemateGeorreferenciado:
        """Intenta localizar el polígono físico de un edicto en el catastro."""
        predio: Optional[PredioCatastral] = None
        canton = edicto.ubicacion.canton if edicto.ubicacion else None
        provider = self._resolver_proveedor(canton)

        # 1. Intentar por número de finca
        if edicto.finca and edicto.finca.numero_finca:
            predio = provider.buscar_por_finca(edicto.finca.numero_finca)

        # 2. Si no se encontró por finca, intentar por plano catastrado
        if not predio and edicto.finca and edicto.finca.plano_catastrado:
            predio = provider.buscar_por_plano(edicto.finca.plano_catastrado)

        return RemateGeorreferenciado(
            folio_real=edicto.finca.folio_real,
            expediente=edicto.expediente,
            acreedor=edicto.acreedor,
            demandado=edicto.demandado,
            base_monto=edicto.base.monto_base,
            moneda=edicto.base.moneda.value,
            predio=predio,
            georreferenciado=predio is not None,
        )

    def georreferenciar_todos_en_bd(
        self, canton: Optional[str] = "Zarcero"
    ) -> List[RemateGeorreferenciado]:
        remates = self.repository.listar(canton=canton, limite=1000)
        resultados: List[RemateGeorreferenciado] = []

        for r in remates:
            geo_r = self.georreferenciar_edicto(r)
            resultados.append(geo_r)

        return resultados

    def exportar_geojson(
        self, remates_geo: List[RemateGeorreferenciado], ruta_salida: str
    ) -> str:
        path = Path(ruta_salida)
        path.parent.mkdir(parents=True, exist_ok=True)

        features: List[Dict[str, Any]] = []

        for item in remates_geo:
            if not item.georreferenciado or not item.predio:
                continue

            predio = item.predio
            props = {
                "folio_real": item.folio_real,
                "expediente": item.expediente or "N/A",
                "acreedor": item.acreedor or "N/A",
                "demandado": item.demandado or "N/A",
                "base_monto": item.base_monto,
                "moneda": item.moneda,
                "distrito": predio.distrito,
                "area_registro_m2": predio.area_registro_m2,
                "area_poligono_m2": predio.area_poligono_m2,
                "frente_m": predio.frente_m,
                "fondo_m": predio.fondo_m,
                "numero_construcciones": predio.numero_construcciones,
                "categoria": predio.categoria,
                "centroide_x": predio.centroide_x,
                "centroide_y": predio.centroide_y,
            }

            feature = {
                "type": "Feature",
                "properties": props,
                "geometry": predio.geometria,
            }
            features.append(feature)

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
