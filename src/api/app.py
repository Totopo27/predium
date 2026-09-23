from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from src.api.routes import api_router

app = FastAPI(
    title="Predium API",
    description="Motor de Inteligencia Inmobiliaria, Catastro y Saneamiento Patrimonial (Costa Rica)",
    version="1.0.0",
)

app.include_router(api_router)

# 1. Montar assets de React si existen
dist_assets = Path("frontend/dist/assets")
if dist_assets.exists():
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="frontend_assets")

# 2. Montar static tradicional de fallback
static_dir = Path("static")
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def home():
    # Preferir frontend React compilado de alta gama
    frontend_dist_index = Path("frontend/dist/index.html")
    if frontend_dist_index.exists():
        return FileResponse(frontend_dist_index)

    # Fallback a prototipo estático
    static_index = Path("static/index.html")
    if static_index.exists():
        return FileResponse(static_index)

    return {"message": "buscaCatastro API activa. Visita /docs para la documentacion interactiva."}
