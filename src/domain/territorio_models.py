from typing import List
from pydantic import BaseModel, Field


class DistritoInfo(BaseModel):
    id: str = Field(..., description="Identificador normalizado del distrito (ej: GUADALUPE)")
    label: str = Field(..., description="Nombre amigable para mostrar en la interfaz")


class TerritorioInfo(BaseModel):
    canton: str = Field(..., description="Nombre oficial del cantón (ej: Zarcero, San Ramón)")
    provincia: str = Field(..., description="Provincia a la que pertenece (ej: Alajuela)")
    codigo_canton: str = Field(..., description="Código DTA de 2 dígitos (ej: 11 para Zarcero, 02 para San Ramón)")
    centro_lng_lat: List[float] = Field(..., description="Coordenadas [longitud, latitud] WGS84 para centrar mapa")
    distritos: List[DistritoInfo] = Field(default_factory=list, description="Lista oficial de distritos")
    proveedor_activo: bool = Field(True, description="Indica si cuenta con WFS municipal de alta resolución")
    descripcion_cobertura: str = Field(..., description="Tipo de cobertura y fuente de datos geográficos")
