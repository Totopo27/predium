import httpx
from bs4 import BeautifulSoup
from datetime import date
from typing import List, Optional
from pathlib import Path
import re


class ImprentaNacionalClient:
    """
    Cliente robusto para interactuar con las publicaciones oficiales de la Imprenta Nacional.
    Incluye sistema de caché en disco y manejo de resiliencia.
    """

    BASE_URL = "https://www.imprentanacional.go.cr/pub-boletin"

    def __init__(self, cache_dir: Optional[str] = "data/cache/boletines", timeout: float = 30.0):
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.client = httpx.Client(
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            },
            follow_redirects=True,
        )

    def construir_url_boletin(self, fecha: date) -> str:
        año = fecha.strftime("%Y")
        mes = fecha.strftime("%m")
        dia = fecha.strftime("%d")
        return f"{self.BASE_URL}/{año}/{mes}/bol_{dia}_{mes}_{año}.html"

    def _ruta_cache(self, fecha: date) -> Optional[Path]:
        if not self.cache_dir:
            return None
        nombre_archivo = f"bol_{fecha.strftime('%d_%m_%Y')}.html"
        return self.cache_dir / nombre_archivo

    def descargar_boletin_html(self, fecha: date) -> Optional[str]:
        """Descarga el Boletín Judicial, usando la caché local si está disponible."""
        # 1. Intentar desde caché local
        ruta_cache = self._ruta_cache(fecha)
        if ruta_cache and ruta_cache.exists():
            try:
                return ruta_cache.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                pass

        # 2. Descargar de la red
        url = self.construir_url_boletin(fecha)
        try:
            response = self.client.get(url)
            if response.status_code == 200:
                response.encoding = response.apparent_encoding or "latin-1"
                contenido = response.text
                # Guardar en caché
                if ruta_cache:
                    try:
                        ruta_cache.write_text(contenido, encoding="utf-8", errors="ignore")
                    except Exception:
                        pass
                return contenido
            return None
        except httpx.HTTPError:
            return None

    def extraer_bloques_remates(self, html_contenido: str) -> List[str]:
        soup = BeautifulSoup(html_contenido, "lxml")
        bloques: List[str] = []
        parrafos = soup.find_all(["p", "div"])

        for elem in parrafos:
            texto = elem.get_text(separator=" ", strip=True)
            if not texto:
                continue

            if re.search(r"\b(?:sáquese a remate|remataré|en el mejor postor remataré|base de)\b", texto, re.IGNORECASE):
                if re.search(r"\b(?:matr[ií]cula|finca|expediente|IN\d+)\b", texto, re.IGNORECASE):
                    bloques.append(texto)

        return bloques
