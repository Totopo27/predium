from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class TipoPersona(str, Enum):
    FISICA = "FISICA"
    JURIDICA = "JURIDICA"


class TitularFinca(BaseModel):
    nombre: str
    cedula: str
    tipo: TipoPersona
    porcentaje_derecho: str = "1/1"


class GravamenTipo(str, Enum):
    HIPOTECA = "HIPOTECA"
    EMBARGO = "EMBARGO"
    DEMANDA = "DEMANDA"
    USUFRUCTO = "USUFRUCTO"
    PATRIMONIO_FAMILIAR = "PATRIMONIO_FAMILIAR"
    BONO_VIVIENDA = "BONO_VIVIENDA"
    SERVIDUMBRE = "SERVIDUMBRE"
    RESERVAS_Y_RESTRICCIONES = "RESERVAS_Y_RESTRICCIONES"
    OTRO = "OTRO"


class Gravamen(BaseModel):
    tipo: GravamenTipo
    descripcion: str
    citas: Optional[str] = None
    acreedor_o_beneficiario: Optional[str] = None
    monto: Optional[float] = None
    moneda: str = "CRC"
    cancelado: bool = False


class EstadoSociedad(str, Enum):
    ACTIVA = "ACTIVA"
    DISUELTA_POR_LEY_9428 = "DISUELTA_POR_LEY_9428"
    EN_LIQUIDACION = "EN_LIQUIDACION"
    MOROSA = "MOROSA"
    NO_APLICA = "NO_APLICA"


class EstrategiaSaneamiento(str, Enum):
    COMPRA_PREVIA_REMATE = "COMPRA_PREVIA_REMATE"
    NUDA_PROPIEDAD_USUFRUCTO = "NUDA_PROPIEDAD_USUFRUCTO"
    LIQUIDACION_SOCIEDAD_DISUELTA = "LIQUIDACION_SOCIEDAD_DISUELTA"
    LIMPIEZA_GRAVAMENES_PRESCRITOS = "LIMPIEZA_GRAVAMENES_PRESCRITOS"
    TITULACION_POSESORIA = "TITULACION_POSESORIA"
    REGULAR = "REGULAR"


class DiagnosticoJuridicoFinca(BaseModel):
    folio_real: str
    titulares: List[TitularFinca] = Field(default_factory=list)
    gravamenes: List[Gravamen] = Field(default_factory=list)
    estado_sociedad: EstadoSociedad = EstadoSociedad.NO_APLICA
    alerta_sociedad_disuelta: bool = False
    alerta_usufructo_activo: bool = False
    alerta_embargos_judiciales: bool = False
    alerta_hipotecas_activas: bool = False
    estrategia_sugerida: EstrategiaSaneamiento = EstrategiaSaneamiento.REGULAR
    diagnostico_resumen: str
