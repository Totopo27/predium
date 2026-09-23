import argparse
import sys
from datetime import date, datetime, timedelta
from src.application.cazar_remates_service import CazarRematesService
from src.application.export_service import ExportService
from src.application.georreferenciar_service import GeorreferenciarService
from src.infrastructure.sqlite_repository import SqliteRemateRepository
from src.infrastructure.catastro_zarcero_client import CatastroZarceroClient

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
            print(f"   {i}. Folio: {e.finca.folio_real} | Plano: {e.finca.plano_catastrado or 'N/A'} | Base: {e.base.moneda.value} {e.base.monto_base:,.2f}")


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

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
