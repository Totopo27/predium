from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field


class InstitucionFinanciera(str, Enum):
    BCR = "BCR"
    BNCR = "BNCR"
    BANCO_POPULAR = "BANCO_POPULAR"
    BAC = "BAC"
    DAVIVIENDA = "DAVIVIENDA"
    GRUPO_MUTUAL = "GRUPO_MUTUAL"
    MUCAP = "MUCAP"
    COOPEALIANZA = "COOPEALIANZA"
    CAJA_DE_ANDE = "CAJA_DE_ANDE"
    OTRO = "OTRO"


class TipoInmuebleBancario(str, Enum):
    CASA = "CASA"
    LOTE_O_TERRENO = "LOTE_O_TERRENO"
    FINCA = "FINCA"
    COMERCIO = "COMERCIO"
    APARTAMENTO = "APARTAMENTO"
    OTRO = "OTRO"


class BienAdjudicado(BaseModel):
    """Representa una propiedad adjudicada/reposeída por una entidad financiera en Costa Rica."""
    id_referencia: str = Field(..., description="Código del banco o identificador único (ej: BCR-BA-1027710922)")
    institucion: InstitucionFinanciera = Field(..., description="Banco, mutual o cooperativa titular del bien")
    folio_real: str = Field(..., description="Matrícula registral estándar: P-NNNNNN-DDD")
    plano_catastrado: Optional[str] = Field(None, description="Número de plano catastrado si está disponible")
    tipo_inmueble: TipoInmuebleBancario = TipoInmuebleBancario.LOTE_O_TERRENO
    provincia: str
    canton: str
    distrito: Optional[str] = None
    descripcion_ubicacion: Optional[str] = None
    area_terreno_m2: Optional[float] = None
    area_construccion_m2: Optional[float] = None
    precio_actual: float = Field(..., description="Precio de venta de liquidación actual")
    precio_original: Optional[float] = Field(None, description="Precio anterior o de avalúo")
    porcentaje_descuento: float = Field(0.0, description="Porcentaje de descuento aplicado (0 a 100)")
    moneda: str = "CRC"  # CRC o USD
    financiamiento_disponible: bool = True
    porcentaje_financiamiento_max: float = 100.0
    url_publicacion: Optional[str] = None
    contacto_nombre: Optional[str] = None
    contacto_telefono: Optional[str] = None
    contacto_email: Optional[str] = None
    fecha_captura: datetime = Field(default_factory=datetime.now)
    geometria: Optional[Dict[str, Any]] = Field(None, description="Geometría GeoJSON del predio una vez cruzado con catastro")
