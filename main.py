import argparse
from datetime import date, datetime, timedelta
from src.application.cazar_remates_service import CazarRematesService


def main():
    parser = argparse.ArgumentParser(
        description="buscaCatastro CLI - Extractor de Edictos de Remate (Costa Rica)"
    )
    parser.add_argument(
        "--canton",
        type=str,
        default="Zarcero",
        help="Cantón a filtrar (default: Zarcero)",
    )
    parser.add_argument(
        "--fecha",
        type=str,
        help="Fecha específica a consultar en formato YYYY-MM-DD",
    )
    parser.add_argument(
        "--dias",
        type=int,
        default=3,
        help="Cantidad de días hábiles hacia atrás a escanear si no se pasa --fecha",
    )

    args = parser.parse_args()

    service = CazarRematesService()

    if args.fecha:
        fecha_obj = datetime.strptime(args.fecha, "%Y-%m-%d").date()
        print(f"\n🔎 Escaneando Boletín Judicial del {fecha_obj} para el cantón: {args.canton}...")
        edictos = service.escanear_fecha(fecha_obj, canton_filtro=args.canton)
    else:
        hoy = date.today()
        desde = hoy - timedelta(days=args.dias)
        print(f"\n🔎 Escaneando rango desde {desde} hasta {hoy} para el cantón: {args.canton}...")
        edictos = service.escanear_rango(desde, hoy, canton_filtro=args.canton)

    if not edictos:
        print(f"ℹ️ No se detectaron edictos de remate para {args.canton} en el período analizado.")
        return

    print(f"\n🎯 ¡Se encontraron {len(edictos)} oportunidades de remate en {args.canton}!\n")
    for i, e in enumerate(edictos, 1):
        print(f"--- [OPORTUNIDAD #{i}] ---")
        print(f"📍 Folio Real:     {e.finca.folio_real}")
        print(f"🗺️ Plano:          {e.finca.plano_catastrado or 'No especificado'}")
        print(f"⚖️ Expediente:     {e.expediente or 'N/A'}")
        print(f"🏛️ Acreedor:       {e.acreedor or 'N/A'}")
        print(f"👤 Demandado:      {e.demandado or 'N/A'}")
        print(f"💰 Base:           {e.base.moneda.value} {e.base.monto_base:,.2f}")
        print(f"📄 Edicto ID:      {e.id_edicto or 'N/A'}")
        print("-" * 35)


if __name__ == "__main__":
    main()
