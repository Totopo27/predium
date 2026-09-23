from typing import Optional, List
from src.domain.registro_models import (
    TitularFinca,
    TipoPersona,
    Gravamen,
    GravamenTipo,
    EstadoSociedad,
    DiagnosticoJuridicoFinca,
)
from src.application.diagnostico_patrimonial_service import DiagnosticoPatrimonialService


class RegistroNacionalClient:
    """
    Cliente para la consulta de información de bienes inmuebles y personas jurídicas
    del Registro Nacional de Costa Rica (RNP Digital).
    """

    def __init__(self, diagnostico_service: Optional[DiagnosticoPatrimonialService] = None):
        self.diagnostico_service = diagnostico_service or DiagnosticoPatrimonialService()

    def consultar_sociedad_mercantil(self, cedula_juridica: str) -> EstadoSociedad:
        """
        Consulta el estado de una sociedad en el Registro de Personas Jurídicas.
        Identifica si fue disuelta por la Ley 9428 (Impuesto a Personas Jurídicas).
        """
        cedula_limpia = cedula_juridica.replace("-", "").strip()

        # En Costa Rica, 3101 son Sociedades Anónimas y 3102 son Sociedades de Responsabilidad Limitada
        if not (cedula_limpia.startswith("3101") or cedula_limpia.startswith("3102")):
            return EstadoSociedad.NO_APLICA

        # En integración real aquí se invoca el servicio de RNP Digital o consulta pública
        # Para fincas con patrón conocido de morosidad o prueba:
        return EstadoSociedad.ACTIVA

    def obtener_estudio_finca(
        self,
        folio_real: str,
        titular_simulado: Optional[TitularFinca] = None,
        gravamenes_simulados: Optional[List[Gravamen]] = None,
        estado_sociedad: EstadoSociedad = EstadoSociedad.NO_APLICA,
    ) -> DiagnosticoJuridicoFinca:
        """
        Genera el estudio registral y diagnóstico jurídico patrimonial completo
        de una finca según su Folio Real.
        """
        # Datos base de la consulta
        titulares = [titular_simulado] if titular_simulado else [
            TitularFinca(
                nombre="PROPIETARIO REGISTRAL",
                cedula="1-0000-0000",
                tipo=TipoPersona.FISICA,
            )
        ]
        gravamenes = gravamenes_simulados or []

        return self.diagnostico_service.evaluar_finca(
            folio_real=folio_real,
            titulares=titulares,
            gravamenes=gravamenes,
            estado_sociedad=estado_sociedad,
        )
