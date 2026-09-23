from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class TipoBienClasificado(str, Enum):
    INMUEBLE = "INMUEBLE"
    VEHICULO = "VEHICULO"
    MUEBLE_OTRO = "MUEBLE_OTRO"


class OrigenDeudaClasificado(str, Enum):
    MUNICIPAL = "MUNICIPAL"
    BANCARIO = "BANCARIO"
    PARTICULAR = "PARTICULAR"


class UrgenciaSubasta(str, Enum):
    PRIMERA = "PRIMERA"
    SEGUNDA = "SEGUNDA"
    TERCERA = "TERCERA"


class ResultadoTriage(BaseModel):
    """Decisión tipada y calibrada emitida por el modelo de Sistema 1."""
    tipo_bien: TipoBienClasificado
    confianza_tipo_bien: float = Field(..., ge=0.0, le=1.0)
    origen_deuda: OrigenDeudaClasificado
    confianza_origen: float = Field(..., ge=0.0, le=1.0)
    es_inmueble: bool
    es_morosidad_municipal: bool
    riesgo_gravamen_complejo: bool
    probabilidad_riesgo: float = Field(..., ge=0.0, le=1.0)
    urgencia: UrgenciaSubasta
    tiempo_inferencia_ms: float
