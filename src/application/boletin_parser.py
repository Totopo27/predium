import re
import unicodedata
from typing import Optional, List, Dict
from src.domain.models import (
    EdictoRemate,
    IdentificadorRegistral,
    UbicacionFinca,
    BaseRemate,
    Moneda,
)

PROVINCIAS_MAP: Dict[str, int] = {
    "san jose": 1,
    "alajuela": 2,
    "cartago": 3,
    "heredia": 4,
    "guanacaste": 5,
    "puntarenas": 6,
    "limon": 7,
}

CANTON_SINONIMOS: Dict[str, List[str]] = {
    "zarcero": ["zarcero", "alfaro ruiz"],
    "alfaro ruiz": ["zarcero", "alfaro ruiz"],
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
        """Determina si el edicto hace referencia a un cantón específico."""
        texto_norm = normalizar_texto(texto)
        canton_norm = normalizar_texto(canton)
        terminos = CANTON_SINONIMOS.get(canton_norm, [canton_norm])
        
        for termino in terminos:
            # Busca variantes como 'canton zarcero', 'canton 11 zarcero', 'zarcero'
            patron = rf"\b(?:canton\s*(?:\d+\s*)?)?{re.escape(termino)}\b"
            if re.search(patron, texto_norm):
                return True
        return False

    def extraer_id_edicto(self, texto: str) -> Optional[str]:
        match = re.search(r"\(\s*(IN\d+)\s*\)", texto, re.IGNORECASE)
        return match.group(1).upper() if match else None

    def extraer_expediente(self, texto: str) -> Optional[str]:
        # Formato judicial típico CR: 23-001234-1200-CJ o similar
        match = re.search(r"expediente\s*[:\s#N°]*([0-9]{2}-[0-9]{5,7}-[0-9]{3,4}-[A-Z0-9\-]+)", texto, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def extraer_partes(self, texto: str) -> tuple[Optional[str], Optional[str]]:
        # de [Acreedor] contra [Demandado], expediente
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
        # Plano: A-1892341-2018 o Plano catastrado número...
        match = re.search(r"[Pp]lano\s*[:\s]*(?:numero\s*|catastrado\s*numero\s*)?([A-Z0-9\-]{5,20})", texto)
        if match:
            return match.group(1).strip()
        return None

    def extraer_finca(self, texto: str) -> Optional[IdentificadorRegistral]:
        # Detectar provincia
        provincia_cod = 2  # Default Alajuela si no se encuentra
        texto_norm = normalizar_texto(texto)
        
        for prov_nombre, cod in PROVINCIAS_MAP.items():
            if f"partido de {prov_nombre}" in texto_norm or f"provincia de {prov_nombre}" in texto_norm:
                provincia_cod = cod
                break

        # Matrícula / número de finca
        # Formatos comunes:
        # "matrícula número 245123-000"
        # "matrícula 2-245123-000"
        # "finca número 245123"
        match_matricula = re.search(r"matr[ií]cula\s*(?:n[uú]mero\s*)?[:\s]*(\d+)[-\s](\d+)", texto, re.IGNORECASE)
        if match_matricula:
            finca_num = match_matricula.group(1)
            derecho = match_matricula.group(2)
            return IdentificadorRegistral(
                provincia_codigo=provincia_cod,
                numero_finca=finca_num,
                derecho=derecho,
                plano_catastrado=self.extraer_plano(texto),
            )

        match_folio_simple = re.search(r"matr[ií]cula\s*(?:n[uú]mero\s*)?[:\s]*(\d+)", texto, re.IGNORECASE)
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
        
        # Identificar provincia
        provincia_detectada = "Alajuela"
        for prov_nombre in PROVINCIAS_MAP.keys():
            if f"provincia de {prov_nombre}" in texto_norm or f"partido de {prov_nombre}" in texto_norm:
                provincia_detectada = prov_nombre.title()
                break

        # Identificar cantón
        canton_detectado = "Desconocido"
        match_canton = re.search(r"cant[oó]n\s*(?:\d+\s*)?([A-Za-z\s]+?)(?:,|\.|\s+de la provincia)", texto, re.IGNORECASE)
        if match_canton:
            canton_detectado = match_canton.group(1).strip()
        elif "zarcero" in texto_norm or "alfaro ruiz" in texto_norm:
            canton_detectado = "Zarcero"

        # Identificar distrito
        distrito_detectado = None
        match_distrito = re.search(r"distrito\s*(?:\d+\s*)?([A-Za-z\s]+?)(?:,|\.|\s+cant[oó]n)", texto, re.IGNORECASE)
        if match_distrito:
            distrito_detectado = match_distrito.group(1).strip()

        return UbicacionFinca(
            provincia=provincia_detectada,
            canton=canton_detectado,
            distrito=distrito_detectado,
        )

    def extraer_base(self, texto: str) -> BaseRemate:
        texto_norm = normalizar_texto(texto)
        moneda = Moneda.USD if "dolares" in texto_norm else Moneda.CRC
        
        # Intenta extraer montos numéricos directos o aproximación
        # Si vienen en texto como "cuarenta y cinco millones", por ahora guardamos 0.0 si no hay dígitos
        # o buscamos cifras explícitas si existen
        match_cifra = re.search(r"(?:[₡$]|base de\s*[:\s]*)([\d\.,]+)", texto)
        monto = 0.0
        if match_cifra:
            raw_num = match_cifra.group(1).replace(".", "").replace(",", ".")
            try:
                monto = float(raw_num)
            except ValueError:
                monto = 0.0

        return BaseRemate(
            moneda=moneda,
            monto_base=monto,
        )

    def parsear_texto_edicto(self, texto: str) -> Optional[EdictoRemate]:
        """Parsea un párrafo de edicto individual y retorna un objeto de dominio EdictoRemate."""
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
