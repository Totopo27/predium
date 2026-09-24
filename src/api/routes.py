from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import date, datetime, timedelta
from src.infrastructure.sqlite_repository import SqliteRemateRepository
from src.infrastructure.sqlite_adjudicados_repository import SqliteAdjudicadosRepository
from src.infrastructure.catastro_factory import CatastroResolver
from src.infrastructure.registro_nacional_client import RegistroNacionalClient
from src.application.georreferenciar_service import GeorreferenciarService
from src.application.gap_analysis_service import GapAnalysisService
from src.application.orchestrator_service import OrchestratorService
from src.domain.registro_models import TitularFinca, TipoPersona, Gravamen, GravamenTipo, EstadoSociedad

api_router = APIRouter(prefix="/api")


@api_router.get("/territorios")
def listar_territorios():
    """Devuelve el catálogo de cantones soportados, centros geográficos y distritos oficiales."""
    return [t.model_dump() for t in CatastroResolver.listar_territorios()]


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
            "tipo_bien": r.tipo_bien,
            "origen_deuda": r.origen_deuda,
            "es_morosidad_municipal": r.es_morosidad_municipal,
            "tipo_oportunidad": r.tipo_oportunidad,
            "viabilidad_saneamiento": r.viabilidad_saneamiento,
            "tiene_gravamen_bloqueante": r.tiene_gravamen_bloqueante,
            "detalles_bloqueo": r.detalles_bloqueo,
            "urgencia": r.urgencia,
            "score_inversion": r.score_inversion,
        }
        for r in remates
    ]


@api_router.get("/adjudicados")
def listar_bienes_adjudicados(
    canton: Optional[str] = "San Ramón",
    institucion: Optional[str] = None,
    limite: int = 50,
):
    from src.domain.adjudicados_models import InstitucionFinanciera
    repo = SqliteAdjudicadosRepository()
    inst_enum = InstitucionFinanciera(institucion) if institucion and institucion in InstitucionFinanciera.__members__ else None
    bienes = repo.listar(canton=canton, institucion=inst_enum, limite=limite)
    return [b.model_dump() for b in bienes]


@api_router.post("/adjudicados/sincronizar")
def sincronizar_bienes_adjudicados(
    canton: Optional[str] = Query("San Ramón", description="Cantón a filtrar"),
):
    from src.application.adjudicados_manager import AdjudicadosManager
    manager = AdjudicadosManager()
    repo = SqliteAdjudicadosRepository()

    encontrados = manager.sincronizar_todos(canton=canton)
    nuevos = repo.guardar_muchos(encontrados)

    return {
        "status": "ok",
        "canton": canton,
        "total_encontrados": len(encontrados),
        "nuevos_guardados": nuevos,
        "mensaje": f"Sincronizados {len(encontrados)} bienes adjudicados ({nuevos} nuevos en BD).",
    }


@api_router.post("/remates/escanear")
def escanear_boletin(
    canton: str = Query("Zarcero", description="Cantón objetivo para el escaneo"),
    dias: int = Query(5, description="Cantidad de días hábiles hacia atrás"),
    fecha: Optional[str] = Query(None, description="Fecha específica en formato YYYY-MM-DD"),
):
    orchestrator = OrchestratorService()

    if fecha:
        try:
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")

        log = orchestrator.ejecutar_ciclo_fecha(fecha=fecha_obj, canton=canton)
        return {
            "status": "ok",
            "canton": canton,
            "fecha_consultada": fecha,
            "total_analizados": log.total_bloques_analizados,
            "inmuebles_detectados": log.inmuebles_detectados,
            "nuevos_guardados": log.nuevos_guardados_bd,
            "georreferenciados": log.georreferenciados_catastro,
            "alertas_emitidas": log.alertas_emitidas,
            "alertas": [a.model_dump() for a in log.alertas],
            "mensaje": f"Escaneo finalizado para {fecha}. Nuevos remates ingresados: {log.nuevos_guardados_bd}.",
        }

    logs = orchestrator.ejecutar_catchup(dias_atras=dias, canton=canton)
    total_nuevos = sum(l.nuevos_guardados_bd for l in logs)
    total_alertas = sum(l.alertas_emitidas for l in logs)
    todas_alertas = []
    for l in logs:
        todas_alertas.extend([a.model_dump() for a in l.alertas])

    return {
        "status": "ok",
        "canton": canton,
        "dias_escaneados": dias,
        "nuevos_guardados": total_nuevos,
        "alertas_emitidas": total_alertas,
        "alertas": todas_alertas,
        "mensaje": f"Escaneo de {dias} días completado. Nuevos remates ingresados: {total_nuevos}.",
    }


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
    canton: Optional[str] = Query("Zarcero", description="Cantón donde se ubica el predio"),
):
    provider = CatastroResolver.obtener_proveedor(canton)
    predio = None
    if finca:
        predio = provider.buscar_por_finca(finca)
    elif plano:
        predio = provider.buscar_por_plano(plano)
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
    canton: str = "Zarcero",
    distrito: str = "TODOS",
    area_min: float = 300.0,
    area_max: float = 80000.0,
    limite_predios: int = 120,
):
    service = GapAnalysisService()

    if distrito.upper() in ("TODOS", "CANTON", "ZARCERO", "COMPLETO"):
        vacios = service.ejecutar_analisis_canton(
            canton=canton,
            area_minima_m2=area_min,
            area_maxima_m2=area_max,
            limite_predios_por_distrito=limite_predios,
        )
    else:
        resultado = service.ejecutar_analisis_distrito(
            distrito=distrito,
            canton=canton,
            area_minima_m2=area_min,
            area_maxima_m2=area_max,
            limite_predios=limite_predios,
        )
        vacios = resultado.vacios if resultado else []

    features = []
    for v in vacios:
        features.append({
            "type": "Feature",
            "properties": {
                "tipo": "VACIO_CATASTRAL",
                "id_vacio": v.id_vacio,
                "distrito": v.distrito,
                "area_m2": v.area_estimada_m2,
                "perimetro_m": v.perimetro_m,
                "colindantes": ", ".join(v.fincas_colindantes[:5]),
                "colindantes_geometrias": v.geometrias_colindantes[:8],
            },
            "geometry": v.geometria,
        })

    return {
        "type": "FeatureCollection",
        "resumen": {
            "distrito_consultado": distrito,
            "total_vacios": len(vacios),
        },
        "features": features,
    }


@api_router.get("/diagnostico")
def diagnosticar_finca(
    folio: str,
    escenario: Optional[str] = None,
):
    """
    Diagnóstico jurídico patrimonial adaptado al contexto real de la finca:
    Si la finca está registrada como remate o adjudicada, hereda su contexto real;
    de lo contrario aplica análisis determinista según sus características.
    """
    client = RegistroNacionalClient()
    repo_remates = SqliteRemateRepository()
    repo_adj = SqliteAdjudicadosRepository()

    # 1. Verificar si existe en la base de remates
    remate_existente = repo_remates.obtener_por_folio_real(folio)
    # 2. Verificar si es un bien adjudicado bancario
    bienes_adj = repo_adj.listar()
    adj_existente = next((b for b in bienes_adj if b.folio_real == folio), None)

    titular = None
    estado_soc = EstadoSociedad.NO_APLICA
    gravamenes = []

    if escenario == "sociedad_disuelta":
        titular = TitularFinca(
            nombre="Desarrollos Inmobiliarios S.A.",
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
        gravamenes.append(Gravamen(tipo=GravamenTipo.USUFRUCTO, descripcion="Usufructo vitalicio"))
    elif adj_existente:
        # Contexto real de bien adjudicado bancario
        titular = TitularFinca(
            nombre=f"{adj_existente.institucion.value} (Entidad Adjudicataria)",
            cedula="3-000-000000",
            tipo=TipoPersona.JURIDICA,
        )
        estado_soc = EstadoSociedad.NO_APLICA
        # Un bien adjudicado ya limpió sus gravámenes judiciales anteriores al adjudicarse
    elif remate_existente:
        # Contexto de ejecución judicial activa
        titular = TitularFinca(
            nombre=remate_existente.demandado or "DEUDOR REGISTRAL",
            cedula="1-0000-0000",
            tipo=TipoPersona.FISICA,
        )
        gravamenes.append(
            Gravamen(
                tipo=GravamenTipo.EMBARGO,
                descripcion=f"Ejecución en expediente {remate_existente.expediente or 'N/A'}",
                acreedor_o_beneficiario=remate_existente.acreedor,
                monto=remate_existente.base.monto_base,
            )
        )
    else:
        # Finca ordinaria sin proceso activo
        titular = TitularFinca(
            nombre="PROPIETARIO REGISTRAL",
            cedula="1-0000-0000",
            tipo=TipoPersona.FISICA,
        )

    diag = client.obtener_estudio_finca(
        folio_real=folio,
        titular_simulado=titular,
        gravamenes_simulados=gravamenes,
        estado_sociedad=estado_soc,
    )

    # Si es bien adjudicado bancario, precisar el dictamen
    if adj_existente:
        dictamen_personalizado = (
            f"Inmueble adjudicado en firme a favor de {adj_existente.institucion.value}. "
            f"El título registral se encuentra libre de los gravámenes anteriores que motivaron el remate. "
            f"Oportunidad de adquisición directa con financiamiento preferencial al precio de liquidación de {adj_existente.moneda} {adj_existente.precio_actual:,.2f}."
        )
        estrategia = "ADQUISICION_BIEN_ADJUDICADO"
    else:
        dictamen_personalizado = diag.diagnostico_resumen
        estrategia = diag.estrategia_sugerida.value

    return {
        "folio_real": diag.folio_real,
        "titular": titular.nombre,
        "cedula": titular.cedula,
        "tipo_titular": titular.tipo.value,
        "alerta_sociedad_disuelta": diag.alerta_sociedad_disuelta,
        "alerta_usufructo_activo": diag.alerta_usufructo_activo,
        "alerta_embargos_judiciales": diag.alerta_embargos_judiciales,
        "estrategia_sugerida": estrategia,
        "dictamen": dictamen_personalizado,
    }
