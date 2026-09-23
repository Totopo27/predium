import argparse
import sys
from datetime import date, datetime, timedelta
from src.application.cazar_remates_service import CazarRematesService
from src.application.export_service import ExportService
from src.infrastructure.sqlite_repository import SqliteRemateRepository

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


def main():
    parser = argparse.ArgumentParser(
        description="buscaCatastro - Modulo de Deteccion de Remates Judiciales y Municipales (Costa Rica)"
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

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
