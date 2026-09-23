import sqlite3
from typing import List, Optional
from datetime import datetime, date
from pathlib import Path
from src.domain.repository_interface import RemateRepository
from src.domain.models import (
    EdictoRemate,
    IdentificadorRegistral,
    UbicacionFinca,
    BaseRemate,
    Moneda,
)


class SqliteRemateRepository(RemateRepository):
    """Implementación de persistencia y deduplicación en SQLite."""

    def __init__(self, db_path: str = "data/remates.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._inicializar_bd()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _inicializar_bd(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS remates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_edicto TEXT UNIQUE,
                    folio_real TEXT NOT NULL,
                    provincia_codigo INTEGER NOT NULL,
                    numero_finca TEXT NOT NULL,
                    derecho TEXT NOT NULL,
                    plano_catastrado TEXT,
                    provincia TEXT NOT NULL,
                    canton TEXT NOT NULL,
                    distrito TEXT,
                    expediente TEXT,
                    juzgado TEXT,
                    acreedor TEXT,
                    demandado TEXT,
                    moneda TEXT NOT NULL,
                    monto_base REAL NOT NULL,
                    monto_segundo_remate REAL,
                    monto_tercer_remate REAL,
                    fecha_publicacion TEXT,
                    estado TEXT DEFAULT 'NUEVO',
                    texto_original TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(folio_real, expediente)
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_remates_canton ON remates(canton)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_remates_folio ON remates(folio_real)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_remates_estado ON remates(estado)"
            )
            conn.commit()

    def guardar(self, edicto: EdictoRemate) -> bool:
        """
        Inserta un edicto o ignora si ya existe la combinación (folio_real, expediente) o id_edicto.
        Retorna True si fue insertado, False si ya existía.
        """
        fecha_pub_str = edicto.fecha_publicacion.isoformat() if edicto.fecha_publicacion else None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO remates (
                        id_edicto, folio_real, provincia_codigo, numero_finca, derecho,
                        plano_catastrado, provincia, canton, distrito, expediente,
                        juzgado, acreedor, demandado, moneda, monto_base,
                        monto_segundo_remate, monto_tercer_remate, fecha_publicacion,
                        texto_original
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        edicto.id_edicto,
                        edicto.finca.folio_real,
                        edicto.finca.provincia_codigo,
                        edicto.finca.numero_finca,
                        edicto.finca.derecho,
                        edicto.finca.plano_catastrado,
                        edicto.ubicacion.provincia,
                        edicto.ubicacion.canton,
                        edicto.ubicacion.distrito,
                        edicto.expediente,
                        edicto.juzgado,
                        edicto.acreedor,
                        edicto.demandado,
                        edicto.base.moneda.value,
                        edicto.base.monto_base,
                        edicto.base.monto_segundo_remate,
                        edicto.base.monto_tercer_remate,
                        fecha_pub_str,
                        edicto.texto_original,
                    ),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # Ya existía (duplicado)
                return False

    def guardar_muchos(self, edictos: List[EdictoRemate]) -> int:
        nuevos = 0
        for e in edictos:
            if self.guardar(e):
                nuevos += 1
        return nuevos

    def _fila_a_modelo(self, row: sqlite3.Row) -> EdictoRemate:
        fecha_pub = (
            date.fromisoformat(row["fecha_publicacion"])
            if row["fecha_publicacion"]
            else None
        )
        return EdictoRemate(
            id_edicto=row["id_edicto"],
            fecha_publicacion=fecha_pub,
            expediente=row["expediente"],
            juzgado=row["juzgado"],
            acreedor=row["acreedor"],
            demandado=row["demandado"],
            finca=IdentificadorRegistral(
                provincia_codigo=row["provincia_codigo"],
                numero_finca=row["numero_finca"],
                derecho=row["derecho"],
                plano_catastrado=row["plano_catastrado"],
            ),
            ubicacion=UbicacionFinca(
                provincia=row["provincia"],
                canton=row["canton"],
                distrito=row["distrito"],
            ),
            base=BaseRemate(
                moneda=Moneda(row["moneda"]),
                monto_base=row["monto_base"],
                monto_segundo_remate=row["monto_segundo_remate"],
                monto_tercer_remate=row["monto_tercer_remate"],
            ),
            texto_original=row["texto_original"],
        )

    def listar(
        self,
        canton: Optional[str] = None,
        estado: Optional[str] = None,
        limite: int = 50,
    ) -> List[EdictoRemate]:
        query = "SELECT * FROM remates WHERE 1=1"
        params = []

        if canton:
            query += " AND LOWER(canton) LIKE ?"
            params.append(f"%{canton.lower()}%")

        if estado:
            query += " AND estado = ?"
            params.append(estado.upper())

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limite)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            filas = cursor.fetchall()
            return [self._fila_a_modelo(r) for r in filas]

    def obtener_por_folio_real(self, folio_real: str) -> Optional[EdictoRemate]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM remates WHERE folio_real = ? LIMIT 1",
                (folio_real,),
            )
            fila = cursor.fetchone()
            return self._fila_a_modelo(fila) if fila else None
