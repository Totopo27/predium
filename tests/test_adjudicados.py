import pytest
from src.domain.adjudicados_models import BienAdjudicado, InstitucionFinanciera, TipoInmuebleBancario
from src.infrastructure.bcr_adjudicados_connector import BcrAdjudicadosConnector
from src.infrastructure.sqlite_adjudicados_repository import SqliteAdjudicadosRepository


def test_parser_texto_bcr():
    connector = BcrAdjudicadosConnector()
    texto_ficticio = """
    Terreno en San Ramón BCR-BA1027710922
    Precio: ¢9.182.400,00
    40% descuento
    ALAJUELA SAN RAMÓN
    Folio real: 2-538150-000
    """
    bienes = connector._parsear_texto_markdown(texto_ficticio, TipoInmuebleBancario.LOTE_O_TERRENO)
    assert len(bienes) == 1
    b = bienes[0]
    assert b.id_referencia == "BCR-BA1027710922"
    assert b.folio_real == "2-538150-000"
    assert b.canton == "San Ramón"
    assert b.precio_actual == 9182400.0
    assert b.porcentaje_descuento == 40.0
    assert b.institucion == InstitucionFinanciera.BCR


def test_repository_adjudicados_guardar_y_deduplicar(tmp_path):
    db_file = tmp_path / "test_adjudicados.db"
    repo = SqliteAdjudicadosRepository(db_path=str(db_file))

    bien = BienAdjudicado(
        id_referencia="BCR-1",
        institucion=InstitucionFinanciera.BCR,
        folio_real="2-538150-000",
        provincia="Alajuela",
        canton="San Ramón",
        precio_actual=9182400.0,
        porcentaje_descuento=40.0,
    )

    assert repo.guardar(bien) is True
    # Segunda inserción debe fallar por deduplicación
    assert repo.guardar(bien) is False

    registros = repo.listar(canton="San Ramón")
    assert len(registros) == 1
    assert registros[0].folio_real == "2-538150-000"
