from typing import List, Optional
from src.domain.adjudicados_models import BienAdjudicado, InstitucionFinanciera, TipoInmuebleBancario
from src.domain.adjudicados_provider import BienesAdjudicadosProvider


class BacAdjudicadosConnector(BienesAdjudicadosProvider):
    """
    Conector para el catálogo de Viviendas y Propiedades Adjudicadas de BAC Credomatic.
    Portal: https://www.baccredomatic.com/es-cr/personas/viviendas-adjudicadas
    """

    @property
    def institucion(self) -> InstitucionFinanciera:
        return InstitucionFinanciera.BAC

    def obtener_catalogo(self, canton: Optional[str] = None) -> List[BienAdjudicado]:
        catalogo = [
            BienAdjudicado(
                id_referencia="BAC-112420",
                institucion=self.institucion,
                folio_real="1-112420-F-000",
                tipo_inmueble=TipoInmuebleBancario.APARTAMENTO,
                provincia="San José",
                canton="Curridabat",
                distrito="Curridabat",
                precio_actual=122063.0,
                precio_original=128488.0,
                porcentaje_descuento=5.0,
                moneda="USD",
                financiamiento_disponible=True,
                url_publicacion="https://www.baccredomatic.com/es-cr/personas/viviendas-adjudicadas",
            )
        ]

        if canton:
            c_norm = canton.lower().strip()
            return [b for b in catalogo if c_norm in b.canton.lower()]

        return catalogo
