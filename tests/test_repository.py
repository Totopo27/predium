import pytest
import os
from src.infrastructure.sqlite_repository import SqliteRemateRepository
from src.domain.models import (
    EdictoRemate,
    IdentificadorRegistral,
    UbicacionFinca,
    BaseRemate,
    Moneda,
)


@pytest.fixture
def repo_temporal(tmp_path):
    db_file = tmp_path / "test_remates.db"
    return SqliteRemateRepository(db_path=str(db_file))


def test_guardar_y_deduplicar(repo_temporal):
    edicto = EdictoRemate(
        id_edicto="IN2024001",
        expediente="23-0001-CJ",
        acreedor="Banco Nacional",
        demandado="Juan Perez",
        finca=IdentificadorRegistral(provincia_codigo=2, numero_finca="123456"),
        ubicacion=UbicacionFinca(provincia="Alajuela", canton="Zarcero", distrito="Laguna"),
        base=BaseRemate(moneda=Moneda.CRC, monto_base=15000000.0),
        texto_original="Texto original de prueba...",
    )

    # Primera inserción -> Debe ser exitosa (True)
    insertado_primera = repo_temporal.guardar(edicto)
    assert insertado_primera is True

    # Segunda inserción del mismo registro -> Debe omitirse por duplicado (False)
    insertado_segunda = repo_temporal.guardar(edicto)
    assert insertado_segunda is False

    # Listar debe devolver exactamente 1 registro
    registros = repo_temporal.listar(canton="Zarcero")
    assert len(registros) == 1
    assert registros[0].finca.folio_real == "2-123456-000"
    assert registros[0].ubicacion.distrito == "Laguna"
