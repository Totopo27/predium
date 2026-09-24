import sqlite3
from typing import List, Optional
from pathlib import Path
from src.domain.adjudicados_models import BienAdjudicado, InstitucionFinanciera, TipoInmuebleBancario
from src.domain.adjudicados_provider import AdjudicadosRepository


class SqliteAdjudicadosRepository(AdjudicadosRepository):
    """Persistencia de bienes adjudicados bancarios en SQLite con modo WAL."""

    def __init__(self, db_path: str = "data/remates.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._inicializar_bd()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _inicializar_bd(self) -> None:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS bienes_adjudicados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_referencia TEXT UNIQUE,
                    institucion TEXT NOT NULL,
                    folio_real TEXT NOT NULL,
                    plano_catastrado TEXT,
                    tipo_inmueble TEXT NOT NULL,
                    provincia TEXT NOT NULL,
                    canton TEXT NOT NULL,
                    distrito TEXT,
                    precio_actual REAL NOT NULL,
                    precio_original REAL,
                    porcentaje_descuento REAL DEFAULT 0,
                    moneda TEXT NOT NULL,
                    financiamiento_disponible INTEGER DEFAULT 1,
                    url_publicacion TEXT,
                    fecha_captura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(institucion, folio_real)
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_adjudicados_canton ON bienes_adjudicados(canton)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_adjudicados_folio ON bienes_adjudicados(folio_real)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_adjudicados_inst ON bienes_adjudicados(institucion)")
            conn.commit()
        finally:
            conn.close()

    def guardar(self, bien: BienAdjudicado) -> bool:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO bienes_adjudicados (
                    id_referencia, institucion, folio_real, plano_catastrado,
                    tipo_inmueble, provincia, canton, distrito, precio_actual,
                    precio_original, porcentaje_descuento, moneda,
                    financiamiento_disponible, url_publicacion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    bien.id_referencia,
                    bien.institucion.value,
                    bien.folio_real,
                    bien.plano_catastrado,
                    bien.tipo_inmueble.value,
                    bien.provincia,
                    bien.canton,
                    bien.distrito,
                    bien.precio_actual,
                    bien.precio_original,
                    bien.porcentaje_descuento,
                    bien.moneda,
                    1 if bien.financiamiento_disponible else 0,
                    bien.url_publicacion,
                ),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def guardar_muchos(self, bienes: List[BienAdjudicado]) -> int:
        nuevos = 0
        for b in bienes:
            if self.guardar(b):
                nuevos += 1
        return nuevos

    def listar(
        self,
        canton: Optional[str] = None,
        institucion: Optional[InstitucionFinanciera] = None,
        limite: int = 50,
    ) -> List[BienAdjudicado]:
        query = "SELECT * FROM bienes_adjudicados WHERE 1=1"
        params = []

        if canton:
            c_clean = canton.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").strip()
            # Búsqueda flexible que tolere acentos tanto en la columna como en el parámetro
            query += " AND (LOWER(canton) LIKE ? OR LOWER(canton) LIKE ?)"
            params.append(f"%{c_clean}%")
            params.append(f"%{canton.lower()}%")

        if institucion:
            query += " AND institucion = ?"
            params.append(institucion.value)

        query += " ORDER BY porcentaje_descuento DESC, id DESC LIMIT ?"
        params.append(limite)

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            filas = cursor.fetchall()
            return [
                BienAdjudicado(
                    id_referencia=r["id_referencia"],
                    institucion=InstitucionFinanciera(r["institucion"]),
                    folio_real=r["folio_real"],
                    plano_catastrado=r["plano_catastrado"],
                    tipo_inmueble=TipoInmuebleBancario(r["tipo_inmueble"]),
                    provincia=r["provincia"],
                    canton=r["canton"],
                    distrito=r["distrito"],
                    precio_actual=r["precio_actual"],
                    precio_original=r["precio_original"],
                    porcentaje_descuento=r["porcentaje_descuento"],
                    moneda=r["moneda"],
                    financiamiento_disponible=bool(r["financiamiento_disponible"]),
                    url_publicacion=r["url_publicacion"],
                )
                for r in filas
            ]
        finally:
            conn.close()
