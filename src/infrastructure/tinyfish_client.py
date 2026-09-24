import os
import httpx
from typing import Optional, Dict, Any


class TinyFishClient:
    """
    Cliente oficial para la API de TinyFish (tinyfish.ai).
    Permite realizar web search estructurado y fetch de páginas dinámicas protegidas por Cloudflare/Akamai/Incapsula.
    """

    BASE_URL = "https://api.tinyfish.ai/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TINYFISH_API_KEY")
        self.client = httpx.Client(
            base_url=self.BASE_URL,
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
                "Content-Type": "application/json",
            },
        )

    @property
    def esta_configurado(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 5)

    def search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Búsqueda web en vivo sin caché, devuelve JSON estructurado (Search API gratuita)."""
        if not self.esta_configurado:
            raise ValueError("TINYFISH_API_KEY no configurada. Obtené una gratis en https://www.tinyfish.ai/")
        resp = self.client.post("/search", json={"query": query, "limit": limit})
        resp.raise_for_status()
        return resp.json()

    def fetch(self, url: str, formato: str = "markdown") -> Dict[str, Any]:
        """Renderiza la página en un navegador real y devuelve contenido limpio (Fetch API gratuita)."""
        if not self.esta_configurado:
            raise ValueError("TINYFISH_API_KEY no configurada. Obtené una gratis en https://www.tinyfish.ai/")
        resp = self.client.post("/fetch", json={"url": url, "format": formato})
        resp.raise_for_status()
        return resp.json()
