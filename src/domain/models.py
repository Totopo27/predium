from enum import Enum
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field


class Moneda(str, Enum):
    CRC = "CRC"
    USD = "USD"


class BaseRemate(BaseModel):
    moneda: Moneda = Moneda.CRC
    monto_base: float = Field(..., description="Monto base inicial (1° subasta)")
    monto_segundo_remate: Optional[float] = Field(None, description="Base rebajada 25% (75% del original)")
    monto_tercer_remate: Optional[float] = Field(None, description="25% de la base original")


class UbicacionFinca(BaseModel):
    provincia: str
    canton: str
    distrito: Optional[str] = None
    detalles: Optional[str] = None


class IdentificadorRegistral(BaseModel):
    provincia_codigo: int = Field(..., ge=1, le=7, description="1: SJ, 2: Alajuela, 3: Cartago, 4: Heredia, 5: Gte, 6: Puntarenas, 7: Limón")
    numero_finca: str
    derecho: str = "000"
    plano_catastrado: Optional[str] = None

    @property
    def folio_real(self) -> str:
        """Retorna formato estándar Folio Real: P-NNNNNN-DDD"""
        return f"{self.provincia_codigo}-{self.numero_finca}-{self.derecho}"


class EdictoRemate(BaseModel):
    id_edicto: Optional[str] = Field(None, description="Código de publicación de la Imprenta Nacional (ej: IN2023820150)")
    fecha_publicacion: Optional[date] = None
    expediente: Optional[str] = None
    juzgado: Optional[str] = None
    acreedor: Optional[str] = None
    demandado: Optional[str] = None
    finca: IdentificadorRegistral
    ubicacion: UbicacionFinca
    medida_m2: Optional[float] = None
    base: BaseRemate
    fechas_subasta: List[datetime] = Field(default_factory=list)
    texto_original: str

    # Dimensiones de Decisión de Sistema 1 (Laya)
    tipo_bien: str = "INMUEBLE"
    origen_deuda: str = "BANCARIO"
    es_morosidad_municipal: bool = False
    tipo_oportunidad: str = "ESTANDAR"
    viabilidad_saneamiento: str = "ALTA"
    tiene_gravamen_bloqueante: bool = False
    detalles_bloqueo: Optional[str] = None
    urgencia: str = "PRIMERA"
    score_inversion: int = 3
