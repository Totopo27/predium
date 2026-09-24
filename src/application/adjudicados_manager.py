from typing import List, Optional
from src.domain.adjudicados_models import BienAdjudicado, InstitucionFinanciera
from src.domain.adjudicados_provider import BienesAdjudicadosProvider
from src.infrastructure.bcr_adjudicados_connector import BcrAdjudicadosConnector
from src.infrastructure.bncr_adjudicados_connector import BncrAdjudicadosConnector
from src.infrastructure.banco_popular_connector import BancoPopularAdjudicadosConnector
from src.infrastructure.bac_adjudicados_connector import BacAdjudicadosConnector
from src.infrastructure.grupo_mutual_connector import GrupoMutualAdjudicadosConnector


class AdjudicadosManager:
    """
    Gestor orquestador de ingesta multi-institucional de bienes adjudicados.
    Coordina los conectores de bancos estatales, bancos privados, mutuales y cooperativas.
    """

    def __init__(self, proveedores: Optional[List[BienesAdjudicadosProvider]] = None):
        self.proveedores: List[BienesAdjudicadosProvider] = proveedores or [
            BcrAdjudicadosConnector(),
            BncrAdjudicadosConnector(),
            BancoPopularAdjudicadosConnector(),
            BacAdjudicadosConnector(),
            GrupoMutualAdjudicadosConnector(),
        ]

    def registrar_proveedor(self, proveedor: BienesAdjudicadosProvider) -> None:
        self.proveedores.append(proveedor)

    def sincronizar_todos(self, canton: Optional[str] = None) -> List[BienAdjudicado]:
        """Recorre todos los bancos e instituciones y unifica el catálogo nacional/cantonal."""
        catalogo_unificado: List[BienAdjudicado] = []
        folios_vistos = set()

        for prov in self.proveedores:
            try:
                encontrados = prov.obtener_catalogo(canton=canton)
                for b in encontrados:
                    if b.folio_real not in folios_vistos:
                        folios_vistos.add(b.folio_real)
                        catalogo_unificado.append(b)
            except Exception:
                pass

        return catalogo_unificado
