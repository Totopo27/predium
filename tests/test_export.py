import json
from pathlib import Path
from src.application.export_service import ExportService
from src.domain.models import (
    EdictoRemate,
    IdentificadorRegistral,
    UbicacionFinca,
    BaseRemate,
    Moneda,
)


def test_exportar_csv_y_json(tmp_path):
    edicto = EdictoRemate(
        id_edicto="IN2024999",
        expediente="24-0002-CJ",
        acreedor="Municipalidad de Zarcero",
        demandado="Empresa X S.A.",
        finca=IdentificadorRegistral(provincia_codigo=2, numero_finca="987654", plano_catastrado="A-55555-2020"),
        ubicacion=UbicacionFinca(provincia="Alajuela", canton="Zarcero", distrito="Tapesco"),
        base=BaseRemate(moneda=Moneda.CRC, monto_base=8500000.0),
        texto_original="Remate tributario...",
    )

    ruta_csv = tmp_path / "test.csv"
    ruta_json = tmp_path / "test.json"

    res_csv = ExportService.exportar_csv([edicto], str(ruta_csv))
    assert Path(res_csv).exists()
    contenido_csv = Path(res_csv).read_text(encoding="utf-8-sig")
    assert "2-987654-000" in contenido_csv
    assert "Municipalidad de Zarcero" in contenido_csv

    res_json = ExportService.exportar_json([edicto], str(ruta_json))
    assert Path(res_json).exists()
    data = json.loads(Path(res_json).read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["finca"]["numero_finca"] == "987654"
