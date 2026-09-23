import re
import unicodedata
from typing import Optional, List, Dict
from datetime import datetime
from src.domain.models import (
    EdictoRemate,
    IdentificadorRegistral,
    UbicacionFinca,
    BaseRemate,
    Moneda,
)
from src.application.text_numbers import palabras_a_numero

PROVINCIAS_MAP: Dict[str, int] = {
    "san jose": 1,
    "alajuela": 2,
    "cartago": 3,
    "heredia": 4,
    "guanacaste": 5,
    "puntarenas": 6,
    "limon": 7,
}

DISTRITOS_ZARCERO = [
    "zarcero",
    "laguna",
    "tapesco",
    "guadalupe",
    "palmira",
    "zapote",
    "brisas",
]

MESES_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "setiembre": 9, "septiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12
}


def normalizar_texto(texto: str) -> str:
    """Elimina tildes y caracteres diacríticos, pasando a minúsculas."""
    texto_norm = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto_norm if not unicodedata.combining(c)).lower()


class BoletinJudicialParser:
    """
    Parser especializado en edictos de remate de bienes inmuebles
    publicados en el Boletín Judicial de Costa Rica (Imprenta Nacional).
    """

    def es_de_canton(self, texto: str, canton: str) -> bool:
        """Determina si el edicto hace referencia a un cantón específico o a sus distritos."""
        texto_norm = normalizar_texto(texto)
        canton_norm = normalizar_texto(canton)

        # Si el cantón es Zarcero, chequear también distritos y sinónimos
        if canton_norm in ("zarcero", "alfaro ruiz"):
            if "zarcero" in texto_norm or "alfaro ruiz" in texto_norm:
                return True
            for dist in DISTRITOS_ZARCERO:
                if re.search(rf"\bdistrito\s*(?:\d+\s*)?{dist}\b", texto_norm):
                    return True
            return False

        patron = rf"\b(?:canton\s*(?:\d+\s*)?)?{re.escape(canton_norm)}\b"
        return bool(re.search(patron, texto_norm))

    def extraer_id_edicto(self, texto: str) -> Optional[str]:
        match = re.search(r"\(\s*(IN\d+)\s*\)", texto, re.IGNORECASE)
        return match.group(1).upper() if match else None

    def extraer_expediente(self, texto: str) -> Optional[str]:
        match = re.search(
            r"expediente\s*[:\s#N°]*([0-9]{2}-[0-9]{5,7}-[0-9]{3,4}-[A-Z0-9\-]+)",
            texto,
            re.IGNORECASE,
        )
        return match.group(1).strip() if match else None

    def extraer_partes(self, texto: str) -> tuple[Optional[str], Optional[str]]:
        match = re.search(
            r"(?:proceso|juicio|ejecucion)\s+[^,\n]+?\s+de\s+(.+?)\s+contra\s+(.+?)(?:,|\.|\s+expediente)",
            texto,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            acreedor = match.group(1).strip().strip(",")
            demandado = match.group(2).strip().strip(",")
            return acreedor, demandado
        return None, None

    def extraer_plano(self, texto: str) -> Optional[str]:
        match = re.search(
            r"[Pp]lano\s*[:\s]*(?:numero\s*|catastrado\s*numero\s*)?([A-Z0-9\-]{5,20})",
            texto,
        )
        return match.group(1).strip() if match else None

    def extraer_finca(self, texto: str) -> Optional[IdentificadorRegistral]:
        provincia_cod = 2  # Default Alajuela
        texto_norm = normalizar_texto(texto)

        for prov_nombre, cod in PROVINCIAS_MAP.items():
            if f"partido de {prov_nombre}" in texto_norm or f"provincia de {prov_nombre}" in texto_norm:
                provincia_cod = cod
                break

        match_matricula = re.search(
            r"matr[ií]cula\s*(?:n[uú]mero\s*)?[:\s]*(\d+)[-\s](\d+)",
            texto,
            re.IGNORECASE,
        )
        if match_matricula:
            return IdentificadorRegistral(
                provincia_codigo=provincia_cod,
                numero_finca=match_matricula.group(1),
                derecho=match_matricula.group(2),
                plano_catastrado=self.extraer_plano(texto),
            )

        match_folio_simple = re.search(
            r"matr[ií]cula\s*(?:n[uú]mero\s*)?[:\s]*(\d+)",
            texto,
            re.IGNORECASE,
        )
        if match_folio_simple:
            return IdentificadorRegistral(
                provincia_codigo=provincia_cod,
                numero_finca=match_folio_simple.group(1),
                derecho="000",
                plano_catastrado=self.extraer_plano(texto),
            )

        return None

    def extraer_ubicacion(self, texto: str) -> UbicacionFinca:
        texto_norm = normalizar_texto(texto)

        provincia_detectada = "Alajuela"
        for prov_nombre in PROVINCIAS_MAP.keys():
            if f"provincia de {prov_nombre}" in texto_norm or f"partido de {prov_nombre}" in texto_norm:
                provincia_detectada = prov_nombre.title()
                break

        canton_detectado = "Zarcero" if ("zarcero" in texto_norm or "alfaro ruiz" in texto_norm) else "Desconocido"
        match_canton = re.search(
            r"cant[oó]n\s*(?:\d+\s*)?([A-Za-z\s]+?)(?:,|\.|\s+de la provincia)",
            texto,
            re.IGNORECASE,
        )
        if match_canton:
            canton_detectado = match_canton.group(1).strip()

        distrito_detectado = None
        match_distrito = re.search(
            r"distrito\s*(?:\d+\s*)?([A-Za-z\s]+?)(?:,|\.|\s+cant[oó]n)",
            texto,
            re.IGNORECASE,
        )
        if match_distrito:
            distrito_detectado = match_distrito.group(1).strip()
        else:
            for dist in DISTRITOS_ZARCERO:
                if dist in texto_norm:
                    distrito_detectado = dist.title()
                    break

        return UbicacionFinca(
            provincia=provincia_detectada,
            canton=canton_detectado,
            distrito=distrito_detectado,
        )

    def extraer_base(self, texto: str) -> BaseRemate:
        texto_norm = normalizar_texto(texto)
        moneda = Moneda.USD if "dolares" in texto_norm else Moneda.CRC

        # Capturar la cláusula de base
        # Ej: "con una base de cuarenta y cinco millones de colones"
        match_base_texto = re.search(r"base de\s+([^,;\.]+?)(?:colones|d[oó]lares|\.|\,)", texto_norm)
        monto_base = 0.0

        if match_base_texto:
            monto_calculado = palabras_a_numero(match_base_texto.group(1))
            if monto_calculado:
                monto_base = monto_calculado

        if monto_base == 0.0:
            match_digitos = re.search(r"[₡$]\s*([\d\.,]+)", texto)
            if match_digitos:
                raw_num = match_digitos.group(1).replace(".", "").replace(",", ".")
                try:
                    monto_base = float(raw_num)
                except ValueError:
                    monto_base = 0.0

        base_2do = round(monto_base * 0.75, 2) if monto_base > 0 else None
        base_3er = round(monto_base * 0.25, 2) if monto_base > 0 else None

        return BaseRemate(
            moneda=moneda,
            monto_base=monto_base,
            monto_segundo_remate=base_2do,
            monto_tercer_remate=base_3er,
        )

    def parsear_texto_edicto(self, texto: str) -> Optional[EdictoRemate]:
        finca = self.extraer_finca(texto)
        if not finca:
            return None

        ubicacion = self.extraer_ubicacion(texto)
        id_edicto = self.extraer_id_edicto(texto)
        expediente = self.extraer_expediente(texto)
        acreedor, demandado = self.extraer_partes(texto)
        base = self.extraer_base(texto)

        return EdictoRemate(
            id_edicto=id_edicto,
            expediente=expediente,
            acreedor=acreedor,
            demandado=demandado,
            finca=finca,
            ubicacion=ubicacion,
            base=base,
            texto_original=texto.strip(),
        )
