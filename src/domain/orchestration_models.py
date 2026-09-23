from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field


class AlertaOportunidad(BaseModel):
    """Representa una oportunidad de negocio detectada con alta prioridad de intervención."""
    tipo_alerta: str = Field(..., description="Ej: MOROSIDAD_MUNICIPAL, TERCERA_SUBASTA, SOCIEDAD_DISUELTA")
    folio_real: str
    expediente: Optional[str] = None
    monto_base: float
    moneda: str
    detalles: str
    prioridad: str = "ALTA"  # MEDIA, ALTA, CRITICA


class CicloIngestaLog(BaseModel):
    """Registro de auditoría y métricas de una ronda de sincronización periódica."""
    id: Optional[int] = None
    fecha_ejecucion: datetime = Field(default_factory=datetime.now)
    fecha_boletin: date
    canton: str
    total_bloques_analizados: int = 0
    inmuebles_detectados: int = 0
    nuevos_guardados_bd: int = 0
    georreferenciados_catastro: int = 0
    alertas_emitidas: int = 0
    alertas: List[AlertaOportunidad] = Field(default_factory=list)
    duracion_segundos: float = 0.0
    estado: str = "EXITOSO"  # EXITOSO, SIN_NOVEDADES, ERROR
    mensaje_error: Optional[str] = None
