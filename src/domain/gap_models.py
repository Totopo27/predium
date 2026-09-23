from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class VacioCatastral(BaseModel):
    """Representa una porción territorial sin registro catastral detectada (eslabón perdido)."""
    id_vacio: str = Field(..., description="Identificador único del vacío detectado")
    distrito: str = Field(..., description="Distrito al que pertenece")
    area_estimada_m2: float = Field(..., description="Superficie aproximada en metros cuadrados")
    perimetro_m: float = Field(..., description="Perímetro en metros")
    centroide_x: float = Field(..., description="Coordenada X (CRTM05)")
    centroide_y: float = Field(..., description="Coordenada Y (CRTM05)")
    fincas_colindantes: List[str] = Field(default_factory=list, description="Números de fincas que delimitan este vacío")
    geometria: Dict[str, Any] = Field(..., description="Geometría GeoJSON del vacío (Polygon o MultiPolygon)")


class ResultadoGapAnalysis(BaseModel):
    """Informe consolidado del análisis de vacíos topológicos para una zona."""
    distrito: str
    area_distrito_m2: float
    area_inscrita_m2: float
    porcentaje_catastrado: float
    total_vacios_detectados: int
    vacios: List[VacioCatastral]
