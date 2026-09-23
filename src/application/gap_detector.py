from typing import List, Dict, Any, Optional
from shapely.geometry import shape, mapping, Polygon, MultiPolygon
from shapely.ops import unary_union
from src.domain.gap_models import VacioCatastral, ResultadoGapAnalysis


class GapDetector:
    """
    Motor de análisis de vacíos topológicos (Gap Analysis).
    Detecta 'eslabones perdidos' mediante diferencia booleana entre el límite distrital
    y los predios formalmente inscritos, filtrando astillas e infraestructura pública.
    """

    def _convertir_a_shapely(self, geom_input: Any) -> Any:
        if isinstance(geom_input, (Polygon, MultiPolygon)):
            return geom_input
        if isinstance(geom_input, dict):
            return shape(geom_input)
        raise ValueError(f"Formato de geometría no soportado: {type(geom_input)}")

    def analizar_zona(
        self,
        distrito_nombre: str,
        geometria_distrito: Any,
        predios_catastrados: List[Dict[str, Any]],
        vias_publicas: Optional[List[Any]] = None,
        cuerpos_agua: Optional[List[Any]] = None,
        area_minima_m2: float = 300.0,
        area_maxima_m2: float = 80000.0,
    ) -> ResultadoGapAnalysis:
        """
        Ejecuta el análisis espacial completo sobre un distrito:
        1. Unión de predios.
        2. Unión de vías y aguas públicas.
        3. Diferencia espacial: Límite - (Predios + Vías + Aguas).
        4. Limpieza de astillas topológicas.
        5. Identificación de fincas colindantes.
        """
        geom_distrito = self._convertir_a_shapely(geometria_distrito)
        area_distrito = float(geom_distrito.area)

        # 1. Preparar geometrías de predios
        sh_predios = []
        for p in predios_catastrados:
            g = self._convertir_a_shapely(p["geometry"])
            if g.is_valid and not g.is_empty:
                sh_predios.append((p.get("finca", "S/F"), g))

        geoms_solo_predios = [g for _, g in sh_predios]
        union_predios = unary_union(geoms_solo_predios) if geoms_solo_predios else Polygon()
        area_inscrita = float(union_predios.area)

        # 2. Preparar exclusiones de dominio público (vías y ríos)
        exclusiones = []
        if vias_publicas:
            for v in vias_publicas:
                gv = self._convertir_a_shapely(v)
                # Si es línea (LineString), aplicar un buffer aproximado de calle (ej. 7m ancho = 3.5m radio)
                if gv.geom_type in ("LineString", "MultiLineString"):
                    gv = gv.buffer(3.5)
                exclusiones.append(gv)

        if cuerpos_agua:
            for a in cuerpos_agua:
                ga = self._convertir_a_shapely(a)
                if ga.geom_type in ("LineString", "MultiLineString"):
                    ga = ga.buffer(5.0)  # Río lineal con zona de cauce
                exclusiones.append(ga)

        union_exclusiones = unary_union(exclusiones) if exclusiones else Polygon()

        # 3. Diferencia espacial (Los vacíos o huecos)
        cobertura_registrada = unary_union([union_predios, union_exclusiones])
        vacios_raw = geom_distrito.difference(cobertura_registrada)

        # 4. Descomponer en polígonos individuales y filtrar astillas
        poligonos_candidatos: List[Polygon] = []
        if isinstance(vacios_raw, Polygon):
            poligonos_candidatos.append(vacios_raw)
        elif isinstance(vacios_raw, MultiPolygon):
            poligonos_candidatos.extend(list(vacios_raw.geoms))

        vacios_detectados: List[VacioCatastral] = []
        contador = 1

        for poly in poligonos_candidatos:
            # Filtro morfológico ligero para eliminar cuellos de botella de 10cm entre límites
            poly_limpio = poly.buffer(-0.5).buffer(0.5)
            area = float(poly_limpio.area)

            if area_minima_m2 <= area <= area_maxima_m2:
                centroide = poly_limpio.centroid
                
                # Identificar fincas que colindan con este vacío
                colindantes: List[str] = []
                geometrias_colindantes: List[Dict[str, Any]] = []
                for finca_id, g_predio in sh_predios:
                    # Si tocan o intersecan el borde del vacío a menos de 2 metros
                    if poly_limpio.distance(g_predio) < 2.0:
                        colindantes.append(finca_id)
                        geometrias_colindantes.append({
                            "finca": finca_id,
                            "area_m2": round(float(g_predio.area), 2),
                            "geometry": mapping(g_predio),
                        })

                vacio_obj = VacioCatastral(
                    id_vacio=f"VACIO-{distrito_nombre.upper().replace(' ', '_')}-{contador:03d}",
                    distrito=distrito_nombre.upper(),
                    area_estimada_m2=round(area, 2),
                    perimetro_m=round(float(poly_limpio.length), 2),
                    centroide_x=round(float(centroide.x), 2),
                    centroide_y=round(float(centroide.y), 2),
                    fincas_colindantes=colindantes,
                    geometrias_colindantes=geometrias_colindantes,
                    geometria=mapping(poly_limpio),
                )
                vacios_detectados.append(vacio_obj)
                contador += 1

        porcentaje_catastrado = (area_inscrita / area_distrito * 100.0) if area_distrito > 0 else 0.0

        return ResultadoGapAnalysis(
            distrito=distrito_nombre.upper(),
            area_distrito_m2=round(area_distrito, 2),
            area_inscrita_m2=round(area_inscrita, 2),
            porcentaje_catastrado=round(porcentaje_catastrado, 2),
            total_vacios_detectados=len(vacios_detectados),
            vacios=vacios_detectados,
        )
