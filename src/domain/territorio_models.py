from typing import List, Optional
from pydantic import BaseModel, Field


class DistritoInfo(BaseModel):
    id: str = Field(..., description="Identificador normalizado del distrito (ej: GUADALUPE)")
    label: str = Field(..., description="Nombre amigable para mostrar en la interfaz")


class PobladoInfo(BaseModel):
    id: str = Field(..., description="Identificador del caserío o poblado (ej: ANATERI)")
    label: str = Field(..., description="Nombre amigable (ej: Anateri - Caserío)")
    distrito_padre: str = Field(..., description="Distrito oficial al que pertenece (ej: GUADALUPE)")


class TerritorioInfo(BaseModel):
    canton: str = Field(..., description="Nombre oficial del cantón (ej: Zarcero, San Ramón)")
    provincia: str = Field(..., description="Provincia a la que pertenece (ej: Alajuela)")
    codigo_canton: str = Field(..., description="Código DTA de 2 dígitos (ej: 11 para Zarcero, 02 para San Ramón)")
    centro_lng_lat: List[float] = Field(..., description="Coordenadas [longitud, latitud] WGS84 para centrar mapa")
    distritos: List[DistritoInfo] = Field(default_factory=list, description="Lista oficial de distritos")
    poblados: List[PobladoInfo] = Field(default_factory=list, description="Caseríos, sectores y poblados destacados")
    proveedor_activo: bool = Field(True, description="Indica si cuenta con WFS municipal de alta resolución")
    descripcion_cobertura: str = Field(..., description="Tipo de cobertura y fuente de datos geográficos")
