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

6. **Módulo 6: Triage Inteligente con Modelos de Sistema 1 (`src/infrastructure/laya_triage_client.py`)**
   - Clasificación no autoregresiva ultrarrápida (<35 ms) con decisiones tipadas y probabilidades calibradas (Laya / ModernBERT / mmBERT).
   - Descarte automático de vehículos y muebles que no son inmuebles.
   - Detección de morosidad fiscal/municipal (*nicho de oro*).
   - Evaluación de riesgo de gravámenes complejos (usufructo, demandas, concesiones de agua) y nivel de urgencia de la subasta (1°, 2° o 3° remate).

7. **Módulo 7: Orquestador y Worker de Ingesta Autónoma (`src/application/orchestrator_service.py` & `src/infrastructure/scheduler.py`)**
   - Pipeline de sincronización autónoma continua con disparador de alertas de negocio.
   - Función de *Catch-up* retrospectivo automático para cubrir fines de semana o cortes de red sin dejar días desatendidos.
   - Alertas críticas automáticas para remates municipales y terceras subastas.

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

### 2. Iniciar el Worker de Sincronización Automática
```powershell
# Ejecución continua cada 6 horas:
python main.py worker --intervalo 6 --canton Zarcero

# Sincronización inmediata de hoy:
python main.py worker --ejecutar-ahora --canton Zarcero

# Barrido retrospectivo (catch-up) de los últimos 5 días hábiles:
python main.py worker --catchup 5 --canton Zarcero
```

### 3. Triage de Edictos con Modelo de Sistema 1 (Laya)
```powershell
python main.py triage --texto "En este Despacho saquese a remate la finca matricula 2-123456-000 en cobro de Municipalidad de Zarcero por impuestos territoriales, soportando usufructo vitalicio."
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
*(24 pruebas unitarias pasando al 100%)*
