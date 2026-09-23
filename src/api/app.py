from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from src.api.routes import api_router

app = FastAPI(
    title="buscaCatastro API",
    description="Motor de Inteligencia Inmobiliaria, Catastro y Saneamiento Patrimonial (Costa Rica)",
    version="1.0.0",
)

app.include_router(api_router)

static_dir = Path("static")
static_dir.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def home():
    index_file = Path("static/index.html")
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "buscaCatastro API activa. Visita /docs para la documentacion interactiva."}
