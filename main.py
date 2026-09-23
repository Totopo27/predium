import argparse
import sys
import webbrowser
from datetime import date, datetime, timedelta
from src.application.cazar_remates_service import CazarRematesService
from src.application.export_service import ExportService
from src.application.georreferenciar_service import GeorreferenciarService
from src.application.gap_analysis_service import GapAnalysisService
from src.application.diagnostico_patrimonial_service import DiagnosticoPatrimonialService
from src.application.orchestrator_service import OrchestratorService
from src.infrastructure.sqlite_repository import SqliteRemateRepository
from src.infrastructure.catastro_zarcero_client import CatastroZarceroClient
from src.infrastructure.registro_nacional_client import RegistroNacionalClient
from src.infrastructure.rnp_scraper_client import RnpScraperClient
from src.infrastructure.laya_triage_client import LayaTriageClient
from src.infrastructure.scheduler import IngestaWorker
from src.domain.registro_models import TitularFinca, TipoPersona, Gravamen, GravamenTipo, EstadoSociedad

# Asegurar UTF-8 en salida estándar para consolas de Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def comando_escanear(args):
    service = CazarRematesService()
    canton = args.canton

    if args.fecha:
        fecha_obj = datetime.strptime(args.fecha, "%Y-%m-%d").date()
        print(f"\n[SCAN] Escaneando Boletin Judicial del {fecha_obj} para: {canton}...")
        edictos, nuevos = service.escanear_fecha(fecha_obj, canton_filtro=canton)
    else:
        hoy = date.today()
        desde = hoy - timedelta(days=args.dias)
        print(f"\n[SCAN] Escaneando desde {desde} hasta {hoy} ({args.dias} dias) para: {canton}...")
        edictos, nuevos = service.escanear_rango(desde, hoy, canton_filtro=canton)

    print(f"\nResultados:")
    print(f"   - Total detectados en publicaciones: {len(edictos)}")
    print(f"   - Nuevos registros ingresados a BD:  {nuevos}")
    print(f"   - Duplicados omitidos:               {len(edictos) - nuevos}")

    if edictos:
        print("\nResumen de fincas detectadas:")
        for i, e in enumerate(edictos, 1):
            tipo_tag = "[MUNICIPAL]" if e.es_morosidad_municipal else "[BANCARIO]"
            print(f"   {i}. {tipo_tag} Folio: {e.finca.folio_real} | Plano: {e.finca.plano_catastrado or 'N/A'} | Base: {e.base.moneda.value} {e.base.monto_base:,.2f}")


def comando_listar(args):
    repo = SqliteRemateRepository()
    remates = repo.listar(canton=args.canton, estado=args.estado, limite=args.limite)

    if not remates:
        print(f"\n[INFO] No hay remates almacenados para el canton: {args.canton or 'Todos'}")
        return

    print(f"\nRemates almacenados en Base de Datos ({len(remates)} encontrados):\n")
    for r in remates:
        print(f"Folio Real:     {r.finca.folio_real}")
        print(f"Plano:          {r.finca.plano_catastrado or 'No especificado'}")
        print(f"Ubicacion:      {r.ubicacion.distrito or 'Centro'}, {r.ubicacion.canton}, {r.ubicacion.provincia}")
        print(f"Expediente:     {r.expediente or 'N/A'}")
        print(f"Acreedor:       {r.acreedor or 'N/A'}")
        print(f"Demandado:      {r.demandado or 'N/A'}")
        print(f"Base:           {r.base.moneda.value} {r.base.monto_base:,.2f}")
        print(f"Edicto:         {r.id_edicto or 'N/A'} (Pub: {r.fecha_publicacion or 'N/A'})")
        print("-" * 50)


def comando_exportar(args):
    repo = SqliteRemateRepository()
    remates = repo.listar(canton=args.canton, limite=1000)

    if not remates:
        print(f"\n[INFO] No hay registros para exportar con el canton: {args.canton or 'Todos'}")
        return

    formato = args.formato.lower()
    salida = args.salida or f"data/remates_{args.canton or 'todos'}.{formato}"

    if formato == "csv":
        ruta = ExportService.exportar_csv(remates, salida)
    elif formato == "json":
        ruta = ExportService.exportar_json(remates, salida)
    else:
        print(f"[ERROR] Formato '{formato}' no soportado. Use 'csv' o 'json'.")
        sys.exit(1)

    print(f"\n[OK] Exportados exitosamente {len(remates)} registros a: {ruta}")


def comando_buscar_predio(args):
    client = CatastroZarceroClient()
    predio = None

    if args.finca:
        print(f"\n[GIS] Consultando WFS Catastro Zarcero por Finca: {args.finca}...")
        predio = client.buscar_por_finca(args.finca)
    elif args.plano:
        print(f"\n[GIS] Consultando WFS Catastro Zarcero por Plano: {args.plano}...")
        predio = client.buscar_por_plano(args.plano)
    else:
        print("[ERROR] Debe especificar --finca o --plano.")
        sys.exit(1)

    if not predio:
        print("[INFO] No se encontro el predio en el mosaico catastral digital de Zarcero.")
        print("       (Posible finca antigua sin georreferenciar, vacio topologico o error de digito).")
        return

    print("\n[OK] Predio encontrado en Catastro Oficial:")
    print(f"   - Finca Catastral:        {predio.finca}")
    print(f"   - Plano Catastrado:       {predio.plano or 'No registrado'}")
    print(f"   - Distrito:               {predio.distrito}")
    print(f"   - Area Segun Registro:    {predio.area_registro_m2 or 'N/A'} m2")
    print(f"   - Area Calculada GIS:     {predio.area_poligono_m2 or 'N/A'} m2")
    print(f"   - Frente / Fondo:         {predio.frente_m or 'N/A'} m / {predio.fondo_m or 'N/A'} m")
    print(f"   - Construcciones:         {predio.numero_construcciones}")
    print(f"   - Categoria:              {predio.categoria}")
    print(f"   - Coordenadas CRTM05:     X={predio.centroide_x}, Y={predio.centroide_y}")
    print(f"   - Tipo de Geometria:      {predio.geometria.get('type')}")


def comando_georreferenciar(args):
    geo_service = GeorreferenciarService()
    print(f"\n[GIS] Cruzando remates en BD con WFS Catastro de {args.canton}...")
    resultados = geo_service.georreferenciar_todos_en_bd(canton=args.canton)

    exitosos = [r for r in resultados if r.georreferenciado]
    print(f"\nResumen de Georreferenciacion:")
    print(f"   - Total procesados en BD: {len(resultados)}")
    print(f"   - Con poligono en mapa:   {len(exitosos)}")
    print(f"   - Sin poligono (gaps):    {len(resultados) - len(exitosos)}")

    if exitosos:
        salida = args.salida or f"data/remates_{args.canton.lower()}_capa.geojson"
        ruta = geo_service.exportar_geojson(resultados, salida)
        print(f"\n[OK] Capa GeoJSON generada exitosamente en: {ruta}")
        print("     (Podes abrirla directamente en QGIS, ArcGIS o en cualquier visor Leaflet).")


def comando_detectar_vacios(args):
    service = GapAnalysisService()
    distrito = args.distrito
    area_min = args.area_min

    print(f"\n[GAP-ANALYSIS] Iniciando deteccion de vacios catastrales en Distrito: {distrito}...")
    print(f"               Umbral de area minima: >= {area_min} m2")

    resultado = service.ejecutar_analisis_distrito(
        distrito=distrito, area_minima_m2=area_min, limite_predios=args.limite_predios
    )

    if not resultado:
        print(f"[ERROR] No se pudo obtener el limite territorial o los predios para {distrito}.")
        return

    print("\n[RESULTADO] Analisis Espacial:")
    print(f"   - Area Total Distrito:       {resultado.area_distrito_m2:,.2f} m2")
    print(f"   - Area Registrada Predios:   {resultado.area_inscrita_m2:,.2f} m2")
    print(f"   - Porcentaje Catastrado:     {resultado.porcentaje_catastrado}%")
    print(f"   - Vacios Topologicos:        {resultado.total_vacios_detectados} detectados")

    if resultado.vacios:
        print("\nTop 5 Vacios con Mayor Potencial (Eslabones Perdidos):")
        for i, v in enumerate(sorted(resultado.vacios, key=lambda x: x.area_estimada_m2, reverse=True)[:5], 1):
            colindantes_str = ", ".join(v.fincas_colindantes[:4]) if v.fincas_colindantes else "Sin datos"
            print(f"   {i}. ID: {v.id_vacio} | Area: {v.area_estimada_m2:,.2f} m2 | Centroide: ({v.centroide_x}, {v.centroide_y}) | Colinda con fincas: {colindantes_str}")

        salida = args.salida or f"data/vacios_{distrito.lower().replace(' ', '_')}.geojson"
        ruta = service.exportar_vacios_geojson(resultado, salida)
        print(f"\n[OK] Capa de vacios exportada a: {ruta}")


def comando_diagnosticar(args):
    folio = args.folio
    print(f"\n[RNP] Ejecutando diagnostico patrimonial para Folio Real: {folio}...")

    if args.archivo:
        scraper = RnpScraperClient()
        print(f"      Procesando archivo registral: {args.archivo}...")
        diag = scraper.parsear_archivo_html(args.archivo, folio_real=folio)
    else:
        client = RegistroNacionalClient()
        titular = None
        estado_soc = EstadoSociedad.NO_APLICA
        gravamenes = []

        if args.escenario == "sociedad_disuelta":
            titular = TitularFinca(
                nombre="Desarrollos del Norte S.A.",
                cedula="3-101-445566",
                tipo=TipoPersona.JURIDICA,
            )
            estado_soc = EstadoSociedad.DISUELTA_POR_LEY_9428
        elif args.escenario == "usufructo":
            titular = TitularFinca(
                nombre="Don Jorge V. (Adulto Mayor)",
                cedula="2-0111-0222",
                tipo=TipoPersona.FISICA,
            )
            gravamenes.append(
                Gravamen(
                    tipo=GravamenTipo.USUFRUCTO,
                    descripcion="Usufructo vitalicio a favor de Don Jorge",
                )
            )
        elif args.escenario == "remate":
            titular = TitularFinca(
                nombre="Inversiones Alfa",
                cedula="3-101-778899",
                tipo=TipoPersona.JURIDICA,
            )
            gravamenes.append(
                Gravamen(
                    tipo=GravamenTipo.EMBARGO,
                    descripcion="Embargo judicial cobratorio",
                    monto=25000000.0,
                )
            )

        diag = client.obtener_estudio_finca(
            folio_real=folio,
            titular_simulado=titular,
            gravamenes_simulados=gravamenes,
            estado_sociedad=estado_soc,
        )

    print("\n--- INFORME DE DIAGNOSTICO JURIDICO ---")
    print(f"Folio Real:               {diag.folio_real}")
    if diag.titulares:
        print(f"Titular:                  {diag.titulares[0].nombre} ({diag.titulares[0].cedula})")
        print(f"Tipo Titular:             {diag.titulares[0].tipo.value}")
    print(f"Gravamenes detectados:    {len(diag.gravamenes)}")
    print(f"Alerta Sociedad Disuelta: {'SI (Ley 9428)' if diag.alerta_sociedad_disuelta else 'NO'}")
    print(f"Alerta Usufructo Activo:  {'SI' if diag.alerta_usufructo_activo else 'NO'}")
    print(f"Alerta Embargos:          {'SI' if diag.alerta_embargos_judiciales else 'NO'}")
    print(f"\nEstrategia Sugerida:      *** {diag.estrategia_sugerida.value} ***")
    print(f"Dictamen Tecnico:         {diag.diagnostico_resumen}")
    print("-" * 50)


def comando_triage(args):
    texto = args.texto
    print("\n[TRIAGE-SISTEMA-1] Analizando texto del edicto con modelo de decision calibrada...")
    client = LayaTriageClient()
    res = client.clasificar_edicto(texto)

    print("\n--- RESULTADO DE CLASIFICACION (SISTEMA 1) ---")
    print(f"Tipo de Bien:             {res.tipo_bien.value} (Confianza: {res.confianza_tipo_bien*100:.1f}%)")
    print(f"Origen de la Deuda:       {res.origen_deuda.value} (Confianza: {res.confianza_origen*100:.1f}%)")
    print(f"Es Inmueble (Target):     {'SI' if res.es_inmueble else 'NO (Descartar)'}")
    print(f"Es Morosidad Municipal:   {'SI (Oportunidad Oro)' if res.es_morosidad_municipal else 'NO'}")
    print(f"Riesgo Legal Complejo:    {'SI' if res.riesgo_gravamen_complejo else 'NO'} (Prob: {res.probabilidad_riesgo*100:.1f}%)")
    print(f"Etapa de Subasta:         {res.urgencia.value}")
    print(f"Latencia de Inferencia:   {res.tiempo_inferencia_ms:.2f} ms")
    print("-" * 50)


def comando_worker(args):
    orchestrator = OrchestratorService()

    if args.catchup:
        print(f"\n[ORQUESTADOR] Iniciando catch-up retrospectivo de {args.catchup} dias para {args.canton}...")
        logs = orchestrator.ejecutar_catchup(dias_atras=args.catchup, canton=args.canton)
        print(f"\n[OK] Catch-up completado. Total de dias procesados: {len(logs)}")
        for l in logs:
            print(f"   - {l.fecha_boletin}: {l.estado} (Nuevos en BD: {l.nuevos_guardados_bd}, Alertas: {l.alertas_emitidas})")
        return

    if args.ejecutar_ahora:
        print(f"\n[ORQUESTADOR] Ejecutando sincronizacion inmediata para {args.canton}...")
        log = orchestrator.ejecutar_ciclo_fecha(fecha=date.today(), canton=args.canton)
        print(f"\n[OK] Ciclo terminado con estado: {log.estado}")
        print(f"   - Nuevos en BD:         {log.nuevos_guardados_bd}")
        print(f"   - Georreferenciados:    {log.georreferenciados_catastro}")
        print(f"   - Alertas de Oportunidad: {log.alertas_emitidas}")
        if log.alertas:
            for a in log.alertas:
                print(f"     🚨 [{a.prioridad}] {a.tipo_alerta}: {a.detalles}")
        return

    worker = IngestaWorker(
        orchestrator=orchestrator,
        cantones=[args.canton],
        intervalo_horas=args.intervalo,
    )
    worker.iniciar_bucle()


def comando_visor(args):
    import uvicorn

    host = args.host
    puerto = args.puerto
    url = f"http://{host}:{puerto}"

    print("\n" + "=" * 55)
    print("🚀 INICIANDO VISOR WEB buscaCatastro")
    print("=" * 55)
    print(f"🌐 Servidor activo en:    {url}")
    print(f"📚 Documentacion API:     {url}/docs")
    print("Presiona Ctrl+C en esta terminal para detener el servidor.\n")

    if not args.no_browser:
        webbrowser.open(url)

    uvicorn.run("src.api.app:app", host=host, port=puerto, reload=False)


def main():
    parser = argparse.ArgumentParser(
        description="buscaCatastro - Plataforma de Inteligencia Inmobiliaria y Catastro (Costa Rica)"
    )
    subparsers = parser.add_subparsers(dest="comando", required=True)

    # Subcomando: escanear
    parser_scan = subparsers.add_parser("escanear", help="Escanea el Boletin Judicial y guarda en BD")
    parser_scan.add_argument("--canton", type=str, default="Zarcero", help="Canton objetivo (default: Zarcero)")
    parser_scan.add_argument("--fecha", type=str, help="Fecha especifica YYYY-MM-DD")
    parser_scan.add_argument("--dias", type=int, default=7, help="Dias hacia atras para escanear (default: 7)")
    parser_scan.set_defaults(func=comando_escanear)

    # Subcomando: listar
    parser_list = subparsers.add_parser("listar", help="Lista los remates almacenados en la BD")
    parser_list.add_argument("--canton", type=str, default="Zarcero", help="Filtrar por canton")
    parser_list.add_argument("--estado", type=str, help="Filtrar por estado (NUEVO, EN_SEGUIMIENTO, etc.)")
    parser_list.add_argument("--limite", type=int, default=20, help="Limite de resultados")
    parser_list.set_defaults(func=comando_listar)

    # Subcomando: exportar
    parser_exp = subparsers.add_parser("exportar", help="Exporta los remates a CSV o JSON")
    parser_exp.add_argument("--canton", type=str, default="Zarcero", help="Canton a exportar")
    parser_exp.add_argument("--formato", type=str, default="csv", choices=["csv", "json"], help="Formato de salida")
    parser_exp.add_argument("--salida", type=str, help="Ruta de archivo destino")
    parser_exp.set_defaults(func=comando_exportar)

    # Subcomando: buscar-predio
    parser_predio = subparsers.add_parser("buscar-predio", help="Consulta directa de un predio al WFS de Zarcero")
    parser_predio.add_argument("--finca", type=str, help="Numero de finca a consultar")
    parser_predio.add_argument("--plano", type=str, help="Numero de plano a consultar")
    parser_predio.set_defaults(func=comando_buscar_predio)

    # Subcomando: georreferenciar
    parser_geo = subparsers.add_parser("georreferenciar", help="Cruza remates con catastro y genera GeoJSON")
    parser_geo.add_argument("--canton", type=str, default="Zarcero", help="Canton a procesar")
    parser_geo.add_argument("--salida", type=str, help="Ruta de salida del GeoJSON")
    parser_geo.set_defaults(func=comando_georreferenciar)

    # Subcomando: detectar-vacios
    parser_vacios = subparsers.add_parser("detectar-vacios", help="Ejecuta el Gap Analysis para cazar eslabones perdidos")
    parser_vacios.add_argument("--distrito", type=str, default="Guadalupe", help="Distrito a analizar (default: Guadalupe)")
    parser_vacios.add_argument("--area-min", type=float, default=500.0, help="Area minima en m2 para filtrar astillas (default: 500)")
    parser_vacios.add_argument("--limite-predios", type=int, default=200, help="Cantidad de predios a procesar")
    parser_vacios.add_argument("--salida", type=str, help="Ruta del GeoJSON de salida")
    parser_vacios.set_defaults(func=comando_detectar_vacios)

    # Subcomando: diagnosticar
    parser_diag = subparsers.add_parser("diagnosticar", help="Diagnostico legal-patrimonial de un Folio Real")
    parser_diag.add_argument("--folio", type=str, required=True, help="Folio Real (ej: 2-120500-000)")
    parser_diag.add_argument(
        "--escenario",
        type=str,
        default="sociedad_disuelta",
        choices=["sociedad_disuelta", "usufructo", "remate", "regular"],
        help="Escenario simulado si no se provee archivo",
    )
    parser_diag.add_argument("--archivo", type=str, help="Ruta a archivo HTML de consulta RNP para parseo real")
    parser_diag.set_defaults(func=comando_diagnosticar)

    # Subcomando: triage
    parser_triage = subparsers.add_parser("triage", help="Ejecuta el triage de Sistema 1 sobre el texto de un edicto")
    parser_triage.add_argument("--texto", type=str, required=True, help="Texto del edicto para clasificar")
    parser_triage.set_defaults(func=comando_triage)

    # Subcomando: worker
    parser_worker = subparsers.add_parser("worker", help="Orquestador autonomo de ingesta y alertas")
    parser_worker.add_argument("--canton", type=str, default="Zarcero", help="Canton objetivo (default: Zarcero)")
    parser_worker.add_argument("--intervalo", type=float, default=6.0, help="Intervalo de ejecucion en horas (default: 6.0)")
    parser_worker.add_argument("--ejecutar-ahora", action="store_true", help="Ejecuta una ronda de sincronizacion inmediata y termina")
    parser_worker.add_argument("--catchup", type=int, help="Ejecuta un catch-up retrospectivo de N dias habiles hacia atras")
    parser_worker.set_defaults(func=comando_worker)

    # Subcomando: visor
    parser_visor = subparsers.add_parser("visor", help="Levanta el Visor Web Interactivo en el navegador")
    parser_visor.add_argument("--puerto", type=int, default=8000, help="Puerto HTTP local (default: 8000)")
    parser_visor.add_argument("--host", type=str, default="127.0.0.1", help="Host local (default: 127.0.0.1)")
    parser_visor.add_argument("--no-browser", action="store_true", help="No abrir el navegador automaticamente")
    parser_visor.set_defaults(func=comando_visor)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
