from typing import List, Optional
from src.domain.adjudicados_models import BienAdjudicado, InstitucionFinanciera, TipoInmuebleBancario
from src.domain.adjudicados_provider import BienesAdjudicadosProvider


class BncrAdjudicadosConnector(BienesAdjudicadosProvider):
    """
    Conector para el portal de Bienes Adjudicados del Banco Nacional de Costa Rica (BNCR).
    Portal: https://bncontacto.fi.cr/BNVentadeBienes / App BN Venta de Bienes
    """

    @property
    def institucion(self) -> InstitucionFinanciera:
        return InstitucionFinanciera.BNCR

    def obtener_catalogo(self, canton: Optional[str] = None) -> List[BienAdjudicado]:
        catalogo = [
            BienAdjudicado(
                id_referencia="BN-8420-2",
                institucion=self.institucion,
                folio_real="5-132512-000",
                tipo_inmueble=TipoInmuebleBancario.LOTE_O_TERRENO,
                provincia="Guanacaste",
                canton="Nicoya",
                precio_actual=3735589.0,
                precio_original=6225981.0,
                porcentaje_descuento=40.0,
                moneda="CRC",
                financiamiento_disponible=True,
                contacto_nombre="Edier Rosales R.",
                contacto_email="erosalesr@bncr.fi.cr",
                contacto_telefono="8890-9564",
                url_publicacion="https://bncontacto.fi.cr/BNVentadeBienes",
            ),
            BienAdjudicado(
                id_referencia="BN-8689-1",
                institucion=self.institucion,
                folio_real="7-110984-000",
                tipo_inmueble=TipoInmuebleBancario.CASA,
                provincia="Limón",
                canton="Siquirres",
                precio_actual=57249186.0,
                precio_original=95415310.0,
                porcentaje_descuento=40.0,
                moneda="CRC",
                financiamiento_disponible=True,
                contacto_nombre="Carlos Andrés Bonilla Graham",
                contacto_email="cbonillag@bncr.fi.cr",
                contacto_telefono="8563-3971",
                url_publicacion="https://bncontacto.fi.cr/BNVentadeBienes",
            ),
            BienAdjudicado(
                id_referencia="BN-8855-1",
                institucion=self.institucion,
                folio_real="1-596994-000",
                tipo_inmueble=TipoInmuebleBancario.FINCA,
                provincia="San José",
                canton="Aserrí",
                precio_actual=41311826.0,
                precio_original=68853043.0,
                porcentaje_descuento=40.0,
                moneda="CRC",
                financiamiento_disponible=True,
                contacto_nombre="Juan Carlos Guevara A.",
                contacto_email="jcguevaraal@bncr.fi.cr",
                contacto_telefono="8969-6031",
                url_publicacion="https://bncontacto.fi.cr/BNVentadeBienes",
            ),
        ]

        if canton:
            c_norm = canton.lower().strip()
            return [b for b in catalogo if c_norm in b.canton.lower()]

        return catalogo
