from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from src.infrastructure.sqlite_repository import SqliteRemateRepository
from src.infrastructure.catastro_zarcero_client import CatastroZarceroClient
from src.infrastructure.registro_nacional_client import RegistroNacionalClient
from src.application.georreferenciar_service import GeorreferenciarService
from src.application.gap_analysis_service import GapAnalysisService
from src.domain.registro_models import TitularFinca, TipoPersona, Gravamen, GravamenTipo, EstadoSociedad

api_router = APIRouter(prefix="/api")


@api_router.get("/remates")
def listar_remates(
    canton: Optional[str] = "Zarcero",
    estado: Optional[str] = None,
    limite: int = 50,
):
    repo = SqliteRemateRepository()
    remates = repo.listar(canton=canton, estado=estado, limite=limite)
    return [
        {
            "id_edicto": r.id_edicto,
            "folio_real": r.finca.folio_real,
            "plano": r.finca.plano_catastrado,
            "canton": r.ubicacion.canton,
            "distrito": r.ubicacion.distrito,
            "expediente": r.expediente,
            "acreedor": r.acreedor,
            "demandado": r.demandado,
            "moneda": r.base.moneda.value,
            "monto_base": r.base.monto_base,
            "monto_segundo": r.base.monto_segundo_remate,
            "monto_tercero": r.base.monto_tercer_remate,
            "fecha_publicacion": r.fecha_publicacion.isoformat() if r.fecha_publicacion else None,
        }
        for r in remates
    ]


@api_router.get("/remates/geojson")
def remates_geojson(canton: Optional[str] = "Zarcero"):
    service = GeorreferenciarService()
    resultados = service.georreferenciar_todos_en_bd(canton=canton)
    
    features = []
    for item in resultados:
        if item.georreferenciado and item.predio:
            p = item.predio
            features.append({
                "type": "Feature",
                "properties": {
                    "tipo": "REMATE",
                    "folio_real": item.folio_real,
                    "expediente": item.expediente,
                    "acreedor": item.acreedor,
                    "demandado": item.demandado,
                    "monto_base": f"{item.moneda} {item.base_monto:,.2f}",
                    "distrito": p.distrito,
                    "area_m2": p.area_registro_m2 or p.area_poligono_m2,
                    "construcciones": p.numero_construcciones,
                },
                "geometry": p.geometria,
            })

    return {
        "type": "FeatureCollection",
        "features": features,
    }


@api_router.get("/catastro/buscar")
def buscar_predio(
    finca: Optional[str] = None,
    plano: Optional[str] = None,
):
    client = CatastroZarceroClient()
    predio = None
    if finca:
        predio = client.buscar_por_finca(finca)
    elif plano:
        predio = client.buscar_por_plano(plano)
    else:
        raise HTTPException(status_code=400, detail="Debe indicar 'finca' o 'plano'")

    if not predio:
        raise HTTPException(status_code=404, detail="Predio no encontrado en catastro")

    return {
        "type": "Feature",
        "properties": {
            "finca": predio.finca,
            "plano": predio.plano,
            "distrito": predio.distrito,
            "area_registro_m2": predio.area_registro_m2,
            "area_poligono_m2": predio.area_poligono_m2,
            "frente_m": predio.frente_m,
            "fondo_m": predio.fondo_m,
            "construcciones": predio.numero_construcciones,
            "categoria": predio.categoria,
            "centroide_x": predio.centroide_x,
            "centroide_y": predio.centroide_y,
        },
        "geometry": predio.geometria,
    }


@api_router.get("/vacios/geojson")
def vacios_geojson(
    distrito: str = "Guadalupe",
    area_min: float = 400.0,
    limite_predios: int = 100,
):
    service = GapAnalysisService()
    resultado = service.ejecutar_analisis_distrito(
        distrito=distrito, area_minima_m2=area_min, limite_predios=limite_predios
    )

    if not resultado:
        return {"type": "FeatureCollection", "features": []}

    features = []
    for v in resultado.vacios:
        features.append({
            "type": "Feature",
            "properties": {
                "tipo": "VACIO_CATASTRAL",
                "id_vacio": v.id_vacio,
                "distrito": v.distrito,
                "area_m2": v.area_estimada_m2,
                "perimetro_m": v.perimetro_m,
                "colindantes": ", ".join(v.fincas_colindantes[:5]),
            },
            "geometry": v.geometria,
        })

    return {
        "type": "FeatureCollection",
        "resumen": {
            "area_distrito_m2": resultado.area_distrito_m2,
            "area_inscrita_m2": resultado.area_inscrita_m2,
            "porcentaje_catastrado": resultado.porcentaje_catastrado,
            "total_vacios": resultado.total_vacios_detectados,
        },
        "features": features,
    }


@api_router.get("/diagnostico")
def diagnosticar_finca(
    folio: str,
    escenario: Optional[str] = "sociedad_disuelta",
):
    client = RegistroNacionalClient()
    titular = None
    estado_soc = EstadoSociedad.NO_APLICA
    gravamenes = []

    if escenario == "sociedad_disuelta":
        titular = TitularFinca(
            nombre="Desarrollos del Norte S.A.",
            cedula="3-101-445566",
            tipo=TipoPersona.JURIDICA,
        )
        estado_soc = EstadoSociedad.DISUELTA_POR_LEY_9428
    elif escenario == "usufructo":
        titular = TitularFinca(
            nombre="Propietario Adulto Mayor",
            cedula="2-0111-0222",
            tipo=TipoPersona.FISICA,
        )
        gravamenes.append(
            Gravamen(tipo=GravamenTipo.USUFRUCTO, descripcion="Usufructo vitalicio")
        )
    elif escenario == "remate":
        titular = TitularFinca(
            nombre="Inversiones Morosas S.A.",
            cedula="3-101-998877",
            tipo=TipoPersona.JURIDICA,
        )
        gravamenes.append(
            Gravamen(tipo=GravamenTipo.EMBARGO, descripcion="Cobro Judicial Bancario", monto=35000000.0)
        )

    diag = client.obtener_estudio_finca(
        folio_real=folio,
        titular_simulado=titular,
        gravamenes_simulados=gravamenes,
        estado_sociedad=estado_soc,
    )

    return {
        "folio_real": diag.folio_real,
        "titular": diag.titulares[0].nombre,
        "cedula": diag.titulares[0].cedula,
        "tipo_titular": diag.titulares[0].tipo.value,
        "alerta_sociedad_disuelta": diag.alerta_sociedad_disuelta,
        "alerta_usufructo_activo": diag.alerta_usufructo_activo,
        "alerta_embargos_judiciales": diag.alerta_embargos_judiciales,
        "estrategia_sugerida": diag.estrategia_sugerida.value,
        "dictamen": diag.diagnostico_resumen,
    }
