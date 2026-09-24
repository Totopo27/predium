from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import date, datetime, timedelta
from src.infrastructure.sqlite_repository import SqliteRemateRepository
from src.infrastructure.sqlite_adjudicados_repository import SqliteAdjudicadosRepository
from src.infrastructure.catastro_factory import CatastroResolver
from src.infrastructure.registro_nacional_client import RegistroNacionalClient
from src.infrastructure.laya_triage_client import LayaTriageClient
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


@api_router.get("/fincas-invisibles")
def listar_fincas_no_georreferenciadas(
    canton: Optional[str] = "Zarcero",
    limite: int = 50,
):
    """
    Auditoría de Fincas Invisibles (Candidatas a Saneamiento):
    Cruza los inmuebles detectados en remates y bancos contra el WFS municipal
    y aísla aquellos con título registral válido que NO existen en el mapa digital.
    Para cada finca invisible, rastrea si existe un Vacío Catastral candidato
    en su mismo distrito y vincula los vecinos colindantes.
    """
    repo_remates = SqliteRemateRepository()
    repo_adj = SqliteAdjudicadosRepository()
    provider = CatastroResolver.obtener_proveedor(canton)
    gap_service = GapAnalysisService()
    triage_client = LayaTriageClient(usar_modelo_local=False)

    remates = repo_remates.listar(canton=canton, limite=limite)
    adjudicados = repo_adj.listar(canton=canton, limite=limite)

    candidatas = []
    folios_vistos = set()

    # Pre-cargar vacíos catastrales del cantón para vincularlos con las fincas invisibles
    vacios_canton = gap_service.ejecutar_analisis_canton(
        canton=canton or "Zarcero",
        area_minima_m2=300.0,
        area_maxima_m2=80000.0,
        limite_predios_por_distrito=100,
    )

    def encontrar_vacio_candidato(distrito_buscado: Optional[str]) -> tuple[Optional[Dict[str, Any]], List[str]]:
        if not distrito_buscado or not vacios_canton:
            return None, []
        d_norm = distrito_buscado.upper().strip()
        for v in vacios_canton:
            if v.distrito.upper() in d_norm or d_norm in v.distrito.upper():
                return {
                    "id_vacio": v.id_vacio,
                    "distrito": v.distrito,
                    "area_m2": v.area_estimada_m2,
                    "perimetro_m": v.perimetro_m,
                    "colindantes": ", ".join(v.fincas_colindantes[:5]),
                    "colindantes_geometrias": v.geometrias_colindantes[:8],
                    "geometry": v.geometria,
                }, v.fincas_colindantes[:5]
        # Si no hay match exacto de distrito pero hay vacíos detectados, ofrecer el primer candidato de zona
        if vacios_canton:
            v_primero = vacios_canton[0]
            return {
                "id_vacio": v_primero.id_vacio,
                "distrito": v_primero.distrito,
                "area_m2": v_primero.area_estimada_m2,
                "perimetro_m": v_primero.perimetro_m,
                "colindantes": ", ".join(v_primero.fincas_colindantes[:5]),
                "colindantes_geometrias": v_primero.geometrias_colindantes[:8],
                "geometry": v_primero.geometria,
            }, v_primero.fincas_colindantes[:5]
        return None, []

    # 1. Auditar fincas adjudicadas por bancos
    for b in adjudicados:
        num_finca = b.folio_real.split("-")[1]
        predio = provider.buscar_por_finca(num_finca)
        if not predio and b.folio_real not in folios_vistos:
            folios_vistos.add(b.folio_real)
            triage = triage_client.clasificar_inmueble(
                texto=f"Inmueble adjudicado por {b.institucion.value} en {b.canton}, folio {b.folio_real}.",
                precio_actual=b.precio_actual,
                porcentaje_descuento=b.porcentaje_descuento,
                no_georreferenciada_wfs=True,
            )
            vacio_candidato, vecinos = encontrar_vacio_candidato(b.distrito)
            candidatas.append({
                "folio_real": b.folio_real,
                "origen": f"Bancario ({b.institucion.value})",
                "tipo_inmueble": b.tipo_inmueble.value,
                "canton": b.canton,
                "distrito": b.distrito or "No asignado en WFS",
                "precio_referencia": f"{b.moneda} {b.precio_actual:,.2f}",
                "descuento": b.porcentaje_descuento,
                "estado_wfs": "Invisible en Catastro Digital (Requiere plano moderno)",
                "tipo_oportunidad": triage.tipo_oportunidad.value,
                "viabilidad_saneamiento": triage.viabilidad_saneamiento.value,
                "detalles_saneamiento": triage.detalles_bloqueo,
                "score_inversion": triage.score_inversion,
                "url_publicacion": b.url_publicacion,
                "vacio_asociado": vacio_candidato,
                "vecinos_colindantes": vecinos,
            })

    # 2. Auditar remates judiciales/municipales
    for r in remates:
        num_finca = r.finca.numero_finca
        predio = provider.buscar_por_finca(num_finca)
        if not predio and r.finca.folio_real not in folios_vistos:
            folios_vistos.add(r.finca.folio_real)
            triage = triage_client.clasificar_inmueble(
                texto=r.texto_original,
                precio_actual=r.base.monto_base,
                no_georreferenciada_wfs=True,
            )
            vacio_candidato, vecinos = encontrar_vacio_candidato(r.ubicacion.distrito)
            candidatas.append({
                "folio_real": r.finca.folio_real,
                "origen": "Cobro Municipal" if r.es_morosidad_municipal else "Cobro Judicial",
                "tipo_inmueble": "Inmueble Registral",
                "canton": r.ubicacion.canton,
                "distrito": r.ubicacion.distrito or "No asignado en WFS",
                "precio_referencia": f"{r.base.moneda.value} {r.base.monto_base:,.2f}",
                "descuento": 25.0 if r.urgencia == "TERCERA" else 0.0,
                "estado_wfs": "Invisible en Catastro Digital (Requiere georreferenciación)",
                "tipo_oportunidad": triage.tipo_oportunidad.value,
                "viabilidad_saneamiento": triage.viabilidad_saneamiento.value,
                "detalles_saneamiento": triage.detalles_bloqueo,
                "score_inversion": triage.score_inversion,
                "expediente": r.expediente,
                "vacio_asociado": vacio_candidato,
                "vecinos_colindantes": vecinos,
            })

    return candidatas


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

    # Si se encuentra en el mapa WFS oficial:
    if predio:
        return {
            "type": "Feature",
            "properties": {
                "tipo": "PREDIO_CATASTRADO",
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

    # Si NO está en el mapa WFS: activar Cazador de Fincas Invisibles (Candidata a Saneamiento)
    num_finca_clean = finca.strip().lstrip("0") if finca else "000000"
    prov_cod = 2
    folio_estimado = f"{prov_cod}-{num_finca_clean}-000"

    repo_remates = SqliteRemateRepository()
    repo_adj = SqliteAdjudicadosRepository()
    remate_existente = repo_remates.obtener_por_folio_real(folio_estimado)
    bienes_adj = repo_adj.listar(canton=canton)
    adj_existente = next((b for b in bienes_adj if num_finca_clean in b.folio_real), None)

    triage_client = LayaTriageClient(usar_modelo_local=False)
    desc_texto = f"Finca {folio_estimado} en cantón {canton} consultada para saneamiento catastral."
    if adj_existente:
        desc_texto += f" Adjudicada por {adj_existente.institucion.value} precio {adj_existente.precio_actual}."
    elif remate_existente:
        desc_texto += f" En proceso de cobro judicial por {remate_existente.acreedor} expediente {remate_existente.expediente}."

    triage = triage_client.clasificar_inmueble(
        texto=desc_texto,
        precio_actual=adj_existente.precio_actual if adj_existente else (remate_existente.base.monto_base if remate_existente else None),
        no_georreferenciada_wfs=True,
    )

    gap_service = GapAnalysisService()
    vacios_canton = gap_service.ejecutar_analisis_canton(canton=canton or "Zarcero", limite_predios_por_distrito=80)
    vacio_asociado = None
    vecinos = []
    if vacios_canton:
        v_cand = vacios_canton[0]
        vacio_asociado = {
            "id_vacio": v_cand.id_vacio,
            "distrito": v_cand.distrito,
            "area_m2": v_cand.area_estimada_m2,
            "perimetro_m": v_cand.perimetro_m,
            "colindantes": ", ".join(v_cand.fincas_colindantes[:5]),
            "colindantes_geometrias": v_cand.geometrias_colindantes[:8],
            "geometry": v_cand.geometria,
        }
        vecinos = v_cand.fincas_colindantes[:5]

    return {
        "type": "Feature",
        "properties": {
            "tipo": "PREDIO_NO_DIGITALIZADO",
            "finca": num_finca_clean,
            "folio_real": folio_estimado,
            "plano": plano or (adj_existente.plano_catastrado if adj_existente else None) or "Sin plano digital",
            "canton": canton,
            "distrito": (adj_existente.distrito if adj_existente else None) or "No asignado en WFS",
            "origen": f"Bancario ({adj_existente.institucion.value})" if adj_existente else ("Cobro Judicial" if remate_existente else "Consulta Directa"),
            "monto_base": f"{adj_existente.moneda} {adj_existente.precio_actual:,.2f}" if adj_existente else (f"{remate_existente.base.moneda.value} {remate_existente.base.monto_base:,.2f}" if remate_existente else "No registrado en cobro"),
            "tipo_oportunidad": triage.tipo_oportunidad.value,
            "viabilidad_saneamiento": triage.viabilidad_saneamiento.value,
            "detalles_bloqueo": triage.detalles_bloqueo,
            "score_inversion": triage.score_inversion,
            "url_publicacion": adj_existente.url_publicacion if adj_existente else None,
            "vacio_asociado": vacio_asociado,
            "vecinos_colindantes": vecinos,
            "detalles": f"Finca con matrícula formal pero sin polígono en el catastro WFS de {canton}. Excelente candidata a saneamiento de linderos.",
        },
        "geometry": vacio_asociado.get("geometry") if vacio_asociado else None,
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
    client = RegistroNacionalClient()
    repo_remates = SqliteRemateRepository()
    repo_adj = SqliteAdjudicadosRepository()

    remate_existente = repo_remates.obtener_por_folio_real(folio)
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
        titular = TitularFinca(
            nombre=f"{adj_existente.institucion.value} (Entidad Adjudicataria)",
            cedula="3-000-000000",
            tipo=TipoPersona.JURIDICA,
        )
        estado_soc = EstadoSociedad.NO_APLICA
    elif remate_existente:
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
