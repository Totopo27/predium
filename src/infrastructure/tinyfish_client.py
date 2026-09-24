import os
from pathlib import Path

# Carga ligera y nativa de variables desde .env sin dependencias externas
def cargar_env_local():
    env_file = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_file.exists():
        try:
            for linea in env_file.read_text(encoding="utf-8").splitlines():
                linea = linea.strip()
                if linea and not linea.startswith("#") and "=" in linea:
                    k, v = linea.split("=", 1)
                    k, v = k.strip(), v.strip().strip("\"'")
                    if k and k not in os.environ:
                        os.environ[k] = v
        except Exception:
            pass

cargar_env_local()

import httpx
from typing import Optional, Dict, Any, List


class TinyFishClient:
    """
    Cliente oficial para la API de TinyFish (tinyfish.ai).
    Permite realizar web search estructurado, fetch de páginas dinámicas y ejecución
    de Web Agent en páginas protegidas por Cloudflare/Akamai/Incapsula.
    """

    BASE_URL = "https://agent.tinyfish.ai/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TINYFISH_API_KEY")
        self.client = httpx.Client(
            timeout=35.0,
            headers={
                "X-API-Key": self.api_key or "",
                "Content-Type": "application/json",
            },
        )

    @property
    def esta_configurado(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 5)

    def search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Búsqueda web en vivo sin caché, devuelve JSON estructurado (Search API gratuita)."""
        if not self.esta_configurado:
            raise ValueError("TINYFISH_API_KEY no configurada. Agregala al archivo .env")
        resp = self.client.post(f"{self.BASE_URL}/search", json={"query": query, "limit": limit})
        resp.raise_for_status()
        return resp.json()

    def fetch(self, urls: List[str] | str, formato: str = "markdown") -> Dict[str, Any]:
        """
        Renderiza las páginas en navegadores reales en la nube y devuelve contenido limpio.
        Acepta una sola URL o una lista de URLs.
        """
        if not self.esta_configurado:
            raise ValueError("TINYFISH_API_KEY no configurada. Agregala al archivo .env")
        urls_lista = [urls] if isinstance(urls, str) else urls
        resp = self.client.post(f"{self.BASE_URL}/fetch", json={"urls": urls_lista, "format": formato})
        resp.raise_for_status()
        return resp.json()

    def run_agent(self, url: str, goal: str) -> Dict[str, Any]:
        """Ejecuta una automatización autónoma navegando y extrayendo datos con browser stealth."""
        if not self.esta_configurado:
            raise ValueError("TINYFISH_API_KEY no configurada. Agregala al archivo .env")
        resp = self.client.post(
            f"{self.BASE_URL}/automation/run",
            json={"url": url, "goal": goal},
        )
        resp.raise_for_status()
        return resp.json()
