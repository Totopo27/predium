# buscaCatastro 📍

**Plataforma de Inteligencia Inmobiliaria, Catastro y Saneamiento Patrimonial (Costa Rica)**

Sistema especializado en detectar, georreferenciar y sanear propiedades en estado de abandono, morosidad fiscal o vulnerabilidad sucesoria mediante el cruce de datos del Boletín Judicial (Imprenta Nacional), Catastro Digital (WFS / SNIT) y Registro Nacional (RNP).

---

## 🏛️ Módulos Implementados

1. **Módulo 1: Extractor y Gestor de Remates (`src/application/cazar_remates_service.py`)**
   - Descarga y segmenta publicaciones oficiales de la Imprenta Nacional.
   - Motor de NLP determinista con conversión de montos en palabras (*"cuarenta y cinco millones"* -> `45,000,000`).
   - Mapeo de los 7 distritos de Zarcero (*Zarcero, Laguna, Tapesco, Guadalupe, Palmira, Zapote, Brisas*).
   - Deduplicación en base de datos SQLite (`data/remates.db`) y exportador a CSV/JSON.

2. **Módulo 2: Integración Geoespacial y Catastro (`src/infrastructure/catastro_zarcero_client.py`)**
   - Conexión WFS 2.0.0 en tiempo real con soporte de filtros CQL.
   - Consulta predial directa por número de finca o plano catastrado.
   - Extracción de geometrías `MultiPolygon` en proyección oficial CRTM05 (EPSG:5367), área de registro, área GIS, frente, fondo y número de construcciones.
   - Arquitectura escalable mediante **Patrón Strategy** (`CatastroProvider`) para admitir cantones con SIG propio y fallback nacional al SNIT central.

3. **Módulo 3: Motor de Detección de Vacíos Catastrales / Gap Analysis (`src/application/gap_detector.py`)**
   - Detección de "eslabones perdidos" (fincas sin dueño/título formal) mediante diferencia booleana espacial (`Diferencia = Límite - Predios Catastrados`).
   - Algoritmo de filtrado de astillas (*slivers*) topológicas.
   - Identificación automática de fincas colindantes que limitan con cada vacío.

4. **Módulo 4: Diagnóstico Jurídico y Saneamiento Patrimonial (`src/application/diagnostico_patrimonial_service.py`)**
   - Evaluación del título registral y emisión de dictamen estratégico:
     - `LIQUIDACION_SOCIEDAD_DISUELTA`: Alerta de extinción por Ley 9428 para compra por debajo de mercado nombrando liquidador notarial/judicial.
     - `NUDA_PROPIEDAD_USUFRUCTO`: Alerta de usufructo vitalicio para estructurar acuerdos de renta/cuidados a adultos mayores.
     - `COMPRA_PREVIA_REMATE`: Alerta de embargos judiciales para rescate antes de la subasta.
     - `LIMPIEZA_GRAVAMENES_PRESCRITOS`: Prescripción de pasivos antiguos.

5. **Módulo 5: Visor Web Interactivo Local (`src/api/` y `static/index.html`)**
   - Servidor montado en FastAPI + Uvicorn.
   - Mapa interactivo Leaflet con ortofoto satelital de alta resolución (Esri Satellite) y calles (OSM).
   - Reproyección al vuelo de coordenadas CRTM05 (EPSG:5367) a WGS84 con `proj4js`.
   - Panel lateral con búsqueda catastral, lista de oportunidades y ficha técnica con evaluación patrimonial.

---

## 🚀 Guía Rápida de Comandos CLI

Para ejecutar los comandos, activa el entorno virtual:
```powershell
.\.venv\Scripts\activate
```

### 1. Iniciar el Visor Web Interactivo en el Navegador
```powershell
python main.py visor
```
> Abre automáticamente `http://127.0.0.1:8000` con el mapa satelital interactivo.

### 2. Escanear Remates en el Boletín Judicial
```powershell
# Escanear los últimos 7 días en Zarcero:
python main.py escanear --canton Zarcero --dias 7

# Escanear una fecha específica:
python main.py escanear --canton Zarcero --fecha 2023-08-21
```

### 3. Listar y Exportar Oportunidades Guardadas
```powershell
# Listar remates almacenados en la base de datos:
python main.py listar --canton Zarcero

# Exportar a CSV para Excel:
python main.py exportar --canton Zarcero --formato csv --salida data/remates_zarcero.csv
```

### 4. Consultar un Predio Directo en el Catastro
```powershell
python main.py buscar-predio --finca 214978
```

### 5. Detectar Vacíos Catastrales (Eslabones Perdidos)
```powershell
python main.py detectar-vacios --distrito Guadalupe --area-min 500
```

### 6. Diagnóstico Legal de un Folio Real
```powershell
python main.py diagnosticar --folio 2-120500-000 --escenario sociedad_disuelta
```

---

## 🧪 Pruebas Automatizadas

El proyecto cuenta con una suite completa de pruebas unitarias y de integración que validan el 100% de la funcionalidad:

```powershell
pytest -v
```
*(17 pruebas unitarias pasando al 100%)*
