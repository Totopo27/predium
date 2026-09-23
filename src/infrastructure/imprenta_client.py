import httpx
from bs4 import BeautifulSoup
from datetime import date
from typing import List, Optional
import re


class ImprentaNacionalClient:
    """Cliente para interactuar con las publicaciones oficiales de la Imprenta Nacional."""

    BASE_URL = "https://www.imprentanacional.go.cr/pub-boletin"

    def __init__(self, timeout: float = 30.0):
        self.client = httpx.Client(
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            },
            follow_redirects=True,
        )

    def construir_url_boletin(self, fecha: date) -> str:
        """Genera la URL esperada para un día hábil dado."""
        año = fecha.strftime("%Y")
        mes = fecha.strftime("%m")
        dia = fecha.strftime("%d")
        return f"{self.BASE_URL}/{año}/{mes}/bol_{dia}_{mes}_{año}.html"

    def descargar_boletin_html(self, fecha: date) -> Optional[str]:
        """Descarga el contenido HTML completo de la edición del Boletín Judicial."""
        url = self.construir_url_boletin(fecha)
        try:
            response = self.client.get(url)
            if response.status_code == 200:
                # Detectar codificación apropiada (latin1 / utf-8 / windows-1252)
                response.encoding = response.apparent_encoding or "latin-1"
                return response.text
            return None
        except httpx.HTTPError:
            return None

    def extraer_bloques_remates(self, html_contenido: str) -> List[str]:
        """
        Extrae los bloques de texto que corresponden a la sección de Remates
        o edictos de subasta de la edición.
        """
        soup = BeautifulSoup(html_contenido, "lxml")
        
        # En la estructura de la Imprenta Nacional, los textos vienen típicamente en párrafos <p>
        # o divs de texto plano.
        bloques: List[str] = []
        parrafos = soup.find_all(["p", "div"])
        
        en_seccion_remates = False
        
        for elem in parrafos:
            texto = elem.get_text(separator=" ", strip=True)
            if not texto:
                continue

            # Detectar encabezados de sección
            if "ADMINISTRACIÓN JUDICIAL" in texto.upper() or "REMATES" in texto.upper():
                en_seccion_remates = True

            # Si encontramos palabras clave de remate de fincas
            if re.search(r"\b(?:sáquese a remate|remataré|en el mejor postor remataré|base de)\b", texto, re.IGNORECASE):
                # Validar que tenga elementos de edicto (matrícula, plano o código IN)
                if re.search(r"\b(?:matr[ií]cula|finca|expediente|IN\d+)\b", texto, re.IGNORECASE):
                    bloques.append(texto)

        return bloques
