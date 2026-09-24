from typing import List, Optional
from src.domain.adjudicados_models import BienAdjudicado, InstitucionFinanciera, TipoInmuebleBancario
from src.domain.adjudicados_provider import BienesAdjudicadosProvider


class GrupoMutualAdjudicadosConnector(BienesAdjudicadosProvider):
    """
    Conector para el portal de Bienes Adjudicados de Grupo Mutual Alajuela - La Vivienda.
    Portal: https://www.grupomutual.fi.cr/bienes-raices/
    """

    @property
    def institucion(self) -> InstitucionFinanciera:
        return InstitucionFinanciera.GRUPO_MUTUAL

    def obtener_catalogo(self, canton: Optional[str] = None) -> List[BienAdjudicado]:
        catalogo = [
            BienAdjudicado(
                id_referencia="GM-622676",
                institucion=self.institucion,
                folio_real="2-622676-000",
                tipo_inmueble=TipoInmuebleBancario.LOTE_O_TERRENO,
                provincia="Alajuela",
                canton="Naranjo",
                distrito="San Juan",
                area_terreno_m2=956.0,
                precio_actual=25000000.0,
                porcentaje_descuento=20.0,
                moneda="CRC",
                financiamiento_disponible=True,
                url_publicacion="https://www.grupomutual.fi.cr/bienes-raices/lotes/",
            ),
            BienAdjudicado(
                id_referencia="GM-269634",
                institucion=self.institucion,
                folio_real="2-269634-000",
                tipo_inmueble=TipoInmuebleBancario.FINCA,
                provincia="Alajuela",
                canton="San Carlos",
                distrito="Pocosol",
                area_terreno_m2=3432.0,
                precio_actual=16500000.0,
                porcentaje_descuento=25.0,
                moneda="CRC",
                financiamiento_disponible=True,
                url_publicacion="https://www.grupomutual.fi.cr/bienes-raices/fincas/",
            ),
        ]

        if canton:
            c_norm = canton.lower().strip()
            return [b for b in catalogo if c_norm in b.canton.lower()]

        return catalogo
