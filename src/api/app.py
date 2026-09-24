import time
import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from src.api.routes import api_router

# Configuración de Logging centralizado del Backend
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("predium.api")

app = FastAPI(
    title="Predium API",
    description="Motor de Inteligencia Inmobiliaria, Catastro y Saneamiento Patrimonial (Costa Rica)",
    version="1.0.0",
)


# Middleware de Auditoría y Tiempos de Respuesta
@app.middleware("http")
async def audit_requests_middleware(request: Request, call_next):
    inicio = time.perf_counter()
    metodo = request.method
    url = str(request.url.path)
    if request.url.query:
        url += f"?{request.url.query}"

    try:
        response = await call_next(request)
        latencia_ms = (time.perf_counter() - inicio) * 1000.0
        codigo = response.status_code

        if codigo >= 400:
            logger.warning(f"HTTP {codigo} | {metodo} {url} | {latencia_ms:.1f}ms")
        else:
            logger.info(f"HTTP {codigo} | {metodo} {url} | {latencia_ms:.1f}ms")

        return response
    except Exception as exc:
        latencia_ms = (time.perf_counter() - inicio) * 1000.0
        logger.error(f"HTTP ERROR 500 | {metodo} {url} | {latencia_ms:.1f}ms | Excepción: {exc}", exc_info=True)
        raise exc


# Rutas API
app.include_router(api_router)

# Montar bundle optimizado de React SPA (dist/assets)
dist_assets = Path("frontend/dist/assets")
if dist_assets.exists():
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="frontend_assets")


@app.get("/")
def home():
    """Sirve la Single Page Application de React o mensaje informativo de API."""
    frontend_dist_index = Path("frontend/dist/index.html")
    if frontend_dist_index.exists():
        return FileResponse(frontend_dist_index)

    return {"message": "Predium API activa. Visita /docs para la documentacion interactiva o corre 'cd frontend && npm run dev'."}
