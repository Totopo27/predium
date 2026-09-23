# Predium 📍

**Plataforma de Inteligencia Inmobiliaria, Catastro Digital y Saneamiento Patrimonial (Costa Rica)**

Predium es un ecosistema proptech diseñado para detectar, georreferenciar y sanear propiedades en desuso, con morosidad tributaria o en vulnerabilidad sucesoria, cruzando datos oficiales del **Boletín Judicial** (Imprenta Nacional), **Catastro Digital WFS** (SNIT/Municipalidades) y el **Registro Nacional de Costa Rica** (RNP).

---

## 🏛️ Arquitectura del Sistema

```
predium/
├── src/
│   ├── domain/               # Entidades puras y Value Objects (Remates, Predios, Diagnósticos)
│   ├── application/          # Casos de uso:
│   │   ├── boletin_parser.py           # NLP determinista para edictos judiciales
│   │   ├── gap_detector.py             # Algoritmo de Gap Analysis espacial (Shapely)
│   │   ├── diagnostico_patrimonial.py  # Motor de dictamen legal y saneamiento
│   │   └── orchestrator_service.py     # Pipeline autónomo y sincronización diaria
│   ├── infrastructure/       # Implementaciones concretas y adaptadores:
│   │   ├── sqlite_repository.py        # Persistencia relacional y deduplicación
│   │   ├── catastro_zarcero_client.py  # Cliente WFS 2.0.0 con filtros CQL
│   │   ├── rnp_scraper_client.py       # Scraper/Parser de informes de rnpdigital.com
│   │   └── laya_triage_client.py       # Modelo de Sistema 1 (<1 ms) para clasificación
│   └── api/                  # Backend REST en FastAPI
├── frontend/                 # Aplicación Web React + Vite + TypeScript + MapLibre GL
├── tests/                    # Suite de 24 pruebas unitarias automatizadas (pytest)
└── main.py                   # CLI unificado de la plataforma
```

---

## ⚡ Capacidades Principales

1. **Cazador de Remates y Morosidad Municipal:**
   - Monitorea publicaciones oficiales del Poder Judicial y detecta remates de fincas por impuestos territoriales impagos (IBI) y deudas bancarias.
   - Extrae el Folio Real (`P-NNNNNN-DDD`), plano catastrado, expediente judicial y bases de subasta (1°, 2° al 75% y 3° al 25%).
2. **Georreferenciación Catastral WFS (Patrón Strategy):**
   - Conexión directa a servidores WFS 2.0.0 oficiales (Zona Piloto: Zarcero, escalable a nivel nacional vía SNIT central).
   - Extrae polígonos `MultiPolygon` en coordenadas oficiales CRTM05 (EPSG:5367), área registrada vs. área física, frente, fondo y número de construcciones.
3. **Detección de Vacíos Catastrales (Gap Analysis):**
   - Algoritmo de diferencia booleana espacial que resta los predios inscritos del límite distrital para cazar **"eslabones perdidos"** (fincas fantasma, baldíos o posesiones históricas en abandono).
4. **Diagnóstico Legal y Estrategias Patrimoniales (RNP):**
   - Identifica inmuebles a nombre de **sociedades disueltas por la Ley N° 9428** para estructurar compras de rescate por debajo del valor de mercado.
   - Detecta **usufructos vitalicios** para acuerdos de nuda propiedad con adultos mayores garantizando renta o cuidados en albergues.
   - Evalúa embargos judiciales para adquisiciones preventivas antes de remates públicos.
5. **Triage de Sistema 1 (<1 ms):**
   - Clasificación ultra-rápida y calibrada basada en **Laya** para descartar vehículos y calificar urgencias sin alucinación.
6. **Visor Web Satelital 2.5D/3D:**
   - Interfaz en **React + MapLibre GL** con ortofoto satelital de alta resolución, reproyección geodésica y fichas de saneamiento.

---

## 🚀 Guía de Inicio Rápido

### Requisitos
- Python 3.12+ (o 3.14)
- Node.js 20+ y npm

### 1. Clonar e Instalar Backend
```bash
git clone https://github.com/Totopo27/predium.git
cd predium

# Crear y activar entorno virtual
python -m venv .venv
# En Windows:
.\.venv\Scripts\activate
# En Linux/Mac:
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Ejecutar la Suite de Pruebas
```bash
pytest -v
```
> Valida el 100% de la lógica con 24 pruebas unitarias automatizadas.

### 3. Iniciar el Backend API y Visor Local
```bash
python main.py visor
```
> Servidor disponible en `http://127.0.0.1:8000` con documentación interactiva en `http://127.0.0.1:8000/docs`.

### 4. Iniciar el Frontend de Desarrollo (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
> Abre tu navegador en `http://localhost:3000` con recarga instantánea HMR.

---

## 🛠️ Comandos CLI Disponibles

```bash
# Sincronización inmediata de remates de hoy:
python main.py worker --ejecutar-ahora --canton Zarcero

# Barrido retrospectivo (catch-up) de los últimos 5 días hábiles:
python main.py worker --catchup 5 --canton Zarcero

# Búsqueda directa de una finca en el catastro WFS:
python main.py buscar-predio --finca 214978

# Detección de vacíos territoriales (Gap Analysis):
python main.py detectar-vacios --distrito Guadalupe --area-min 500

# Diagnóstico jurídico de un Folio Real:
python main.py diagnosticar --folio 2-120500-000 --escenario sociedad_disuelta

# Triage de Sistema 1 sobre el texto de un edicto:
python main.py triage --texto "Sáquese a remate finca del partido de Alajuela..."
```

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.
