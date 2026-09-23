import csv
import json
from typing import List
from pathlib import Path
from src.domain.models import EdictoRemate


class ExportService:
    """Servicio para exportar los remates a formatos estándar (CSV, JSON)."""

    @staticmethod
    def exportar_csv(edictos: List[EdictoRemate], ruta_archivo: str) -> str:
        path = Path(ruta_archivo)
        path.parent.mkdir(parents=True, exist_ok=True)

        campos = [
            "folio_real",
            "plano_catastrado",
            "provincia",
            "canton",
            "distrito",
            "expediente",
            "acreedor",
            "demandado",
            "moneda",
            "monto_base",
            "monto_segundo_remate",
            "monto_tercer_remate",
            "fecha_publicacion",
            "id_edicto",
        ]

        with open(path, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=campos)
            writer.writeheader()
            for e in edictos:
                writer.writerow(
                    {
                        "folio_real": e.finca.folio_real,
                        "plano_catastrado": e.finca.plano_catastrado or "",
                        "provincia": e.ubicacion.provincia,
                        "canton": e.ubicacion.canton,
                        "distrito": e.ubicacion.distrito or "",
                        "expediente": e.expediente or "",
                        "acreedor": e.acreedor or "",
                        "demandado": e.demandado or "",
                        "moneda": e.base.moneda.value,
                        "monto_base": e.base.monto_base,
                        "monto_segundo_remate": e.base.monto_segundo_remate or "",
                        "monto_tercer_remate": e.base.monto_tercer_remate or "",
                        "fecha_publicacion": e.fecha_publicacion.isoformat() if e.fecha_publicacion else "",
                        "id_edicto": e.id_edicto or "",
                    }
                )

        return str(path)

    @staticmethod
    def exportar_json(edictos: List[EdictoRemate], ruta_archivo: str) -> str:
        path = Path(ruta_archivo)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = [json.loads(e.model_dump_json()) for e in edictos]
        with open(path, mode="w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return str(path)
