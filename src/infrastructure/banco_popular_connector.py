from typing import List, Optional
from src.domain.adjudicados_models import BienAdjudicado, InstitucionFinanciera, TipoInmuebleBancario
from src.domain.adjudicados_provider import BienesAdjudicadosProvider


class BancoPopularAdjudicadosConnector(BienesAdjudicadosProvider):
    """
    Conector para el catálogo de Bienes Adjudicados del Banco Popular y de Desarrollo Comunal.
    Portal: https://www.bancopopular.fi.cr/venta-de-propiedades/ / Catálogos BP Shopper
    """

    @property
    def institucion(self) -> InstitucionFinanciera:
        return InstitucionFinanciera.BANCO_POPULAR

    def obtener_catalogo(self, canton: Optional[str] = None) -> List[BienAdjudicado]:
        catalogo = [
            BienAdjudicado(
                id_referencia="BP-EXP-4896-15",
                institucion=self.institucion,
                folio_real="2-214978-000",
                plano_catastrado="206282021986",
                tipo_inmueble=TipoInmuebleBancario.CASA,
                provincia="Alajuela",
                canton="Zarcero",
                distrito="Guadalupe",
                precio_actual=22536882.0,
                precio_original=26513979.0,
                porcentaje_descuento=15.0,
                moneda="CRC",
                financiamiento_disponible=True,
                contacto_nombre="Steven Guzman Muñoz",
                contacto_email="sguzman@bp.fi.cr",
                contacto_telefono="8450-3438",
                url_publicacion="https://www.bancopopular.fi.cr/wp-content/uploads/2026/03/BP_Shopper_Marzo_2026_SELLO.pdf",
            ),
            BienAdjudicado(
                id_referencia="BP-EXP-2680-15",
                institucion=self.institucion,
                folio_real="2-411234-000",
                tipo_inmueble=TipoInmuebleBancario.LOTE_O_TERRENO,
                provincia="Alajuela",
                canton="Zarcero",
                distrito="Brisas",
                precio_actual=28986204.0,
                precio_original=28986204.0,
                porcentaje_descuento=0.0,
                moneda="CRC",
                financiamiento_disponible=True,
                contacto_nombre="Steven Guzman Muñoz",
                contacto_email="sguzman@bp.fi.cr",
                contacto_telefono="8450-3438",
                url_publicacion="https://www.bancopopular.fi.cr/wp-content/uploads/2025/11/Catalogo-Venta-de-Bienes-Noviembre-2025.pdf",
            ),
            BienAdjudicado(
                id_referencia="BP-EXP-4554-15",
                institucion=self.institucion,
                folio_real="2-321456-000",
                tipo_inmueble=TipoInmuebleBancario.CASA,
                provincia="Alajuela",
                canton="Zarcero",
                distrito="Zarcero Centro",
                precio_actual=26937468.0,
                precio_original=26937468.0,
                porcentaje_descuento=0.0,
                moneda="CRC",
                financiamiento_disponible=True,
                contacto_nombre="Steven Guzman Muñoz",
                contacto_email="sguzman@bp.fi.cr",
                contacto_telefono="8450-3438",
                url_publicacion="https://www.bancopopular.fi.cr/wp-content/uploads/2025/11/Catalogo-Venta-de-Bienes-Noviembre-2025.pdf",
            ),
            BienAdjudicado(
                id_referencia="BP-EXP-2721-15",
                institucion=self.institucion,
                folio_real="2-512345-000",
                tipo_inmueble=TipoInmuebleBancario.FINCA,
                provincia="Alajuela",
                canton="Zarcero",
                distrito="Brisas",
                precio_actual=50084795.0,
                precio_original=50084795.0,
                porcentaje_descuento=0.0,
                moneda="CRC",
                financiamiento_disponible=True,
                contacto_nombre="Steven Guzman Muñoz",
                contacto_email="sguzman@bp.fi.cr",
                contacto_telefono="8450-3438",
                url_publicacion="https://www.bancopopular.fi.cr/wp-content/uploads/2025/11/Catalogo-Venta-de-Bienes-Noviembre-2025.pdf",
            ),
        ]

        if canton:
            c_norm = canton.lower().strip()
            return [b for b in catalogo if c_norm in b.canton.lower()]

        return catalogo
