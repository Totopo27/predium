from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class PredioCatastral(BaseModel):
    """Representa un predio o lote oficial en el catastro municipal/nacional."""
    finca: str = Field(..., description="Número de finca registrado en el catastro")
    plano: Optional[str] = Field(None, description="Número de plano catastrado asociado")
    distrito: str = Field(..., description="Nombre del distrito (ej: ZARCERO, GUADALUPE)")
    area_registro_m2: Optional[float] = Field(None, description="Área en m2 según registro")
    area_poligono_m2: Optional[float] = Field(None, description="Área en m2 calculada del polígono GIS")
    frente_m: Optional[float] = Field(None, description="Metros de frente a calle pública")
    fondo_m: Optional[float] = Field(None, description="Metros de fondo del lote")
    numero_construcciones: int = Field(0, description="Cantidad de edificaciones registradas")
    categoria: str = Field("Finca Inscrita", description="Categoría catastral")
    centroide_x: float = Field(..., description="Coordenada X en proyección CRTM05")
    centroide_y: float = Field(..., description="Coordenada Y en proyección CRTM05")
    geometria: Dict[str, Any] = Field(..., description="Geometría GeoJSON (Polygon o MultiPolygon)")


class RemateGeorreferenciado(BaseModel):
    """Cruce enriquecido entre un edicto de remate legal y su polígono catastral físico."""
    folio_real: str
    expediente: Optional[str] = None
    acreedor: Optional[str] = None
    demandado: Optional[str] = None
    base_monto: float
    moneda: str
    predio: Optional[PredioCatastral] = None
    georreferenciado: bool = False
