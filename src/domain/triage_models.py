from enum import Enum
from typing import Optional, Dict, Any, List
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
    VENTA_DIRECTA = "VENTA_DIRECTA"


class TipoOportunidadNegocio(str, Enum):
    ABANDONO_FISCAL = "ABANDONO_FISCAL"                # Cobro municipal de impuestos (IBI)
    LIQUIDACION_BANCARIA = "LIQUIDACION_BANCARIA"      # Bien adjudicado por entidad financiera
    VULNERABILIDAD_PATRIMONIAL = "VULNERABILIDAD_PATRIMONIAL"  # Usufructo / Adulto mayor / Sucesión
    LITIGIO_COMPLEJO = "LITIGIO_COMPLEJO"              # Múltiples acreedores / embargos cruzados
    ESTANDAR = "ESTANDAR"


class ViabilidadSaneamiento(str, Enum):
    ALTA = "ALTA"      # Título expedito o gravamen cancelable con la subasta
    MEDIA = "MEDIA"    # Requiere trámite notarial (nombramiento liquidador, prescripción)
    BAJA = "BAJA"      # Afectaciones institucionales (BANHVI, patrimonio familiar sin acuerdo)


class ResultadoTriageAvanzado(BaseModel):
    """Evaluación holística calibrada emitida por el modelo de Sistema 1 (Laya)."""
    # 1. Filtro primario
    tipo_bien: TipoBienClasificado
    confianza_tipo_bien: float = Field(..., ge=0.0, le=1.0)
    es_inmueble: bool

    # 2. Origen del crédito
    origen_deuda: OrigenDeudaClasificado
    confianza_origen: float = Field(..., ge=0.0, le=1.0)
    es_morosidad_municipal: bool

    # 3. Clasificación de Oportunidad de Negocio
    tipo_oportunidad: TipoOportunidadNegocio
    confianza_oportunidad: float = Field(0.90, ge=0.0, le=1.0)

    # 4. Viabilidad y Riesgos Bloqueantes
    viabilidad_saneamiento: ViabilidadSaneamiento
    tiene_gravamen_bloqueante: bool
    probabilidad_bloqueo: float = Field(..., ge=0.0, le=1.0)
    detalles_bloqueo: Optional[str] = None

    # 5. Nivel de Urgencia y Score de Inversión
    urgencia: UrgenciaSubasta
    score_inversion: int = Field(..., ge=1, le=5, description="1: Poco atractiva, 5: Oportunidad de oro")
    tiempo_inferencia_ms: float
