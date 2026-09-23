import time
import sys
from datetime import date, datetime
from typing import Optional, List
from src.application.orchestrator_service import OrchestratorService


class IngestaWorker:
    """
    Worker autónomo de sincronización e ingesta continua.
    Monitorea publicaciones del Boletín Judicial, ejecuta el pipeline completo y emite alertas.
    """

    def __init__(
        self,
        orchestrator: Optional[OrchestratorService] = None,
        cantones: Optional[List[str]] = None,
        intervalo_horas: float = 6.0,
    ):
        self.orchestrator = orchestrator or OrchestratorService()
        self.cantones = cantones or ["Zarcero"]
        self.intervalo_segundos = max(60.0, intervalo_horas * 3600.0)
        self.detenido = False

    def ejecutar_ronda(self) -> None:
        """Ejecuta una ronda de sincronización para todos los cantones configurados."""
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hoy = date.today()
        print(f"\n[{ahora}] [WORKER] Iniciando ronda de sincronizacion para {self.cantones}...")

        for canton in self.cantones:
            log = self.orchestrator.ejecutar_ciclo_fecha(fecha=hoy, canton=canton)
            print(f"[{canton}] Estado: {log.estado} | Nuevos en BD: {log.nuevos_guardados_bd} | Georreferenciados: {log.georreferenciados_catastro} | Duracion: {log.duracion_segundos}s")

            if log.alertas:
                print(f"🚨 ALERTA DE OPORTUNIDAD: {len(log.alertas)} detectadas en {canton}:")
                for a in log.alertas:
                    print(f"   - [{a.prioridad}] {a.tipo_alerta} en Folio {a.folio_real}: {a.detalles}")

    def iniciar_bucle(self) -> None:
        """Inicia el servicio en segundo plano de ejecución continua."""
        print("=" * 60)
        print("🤖 WORKER AUTONOMO DE INGESTA buscaCatastro")
        print(f"⏰ Intervalo de ejecucion: cada {self.intervalo_segundos / 3600.0:.1f} horas")
        print(f"📍 Cantones activos:      {self.cantones}")
        print("Presiona Ctrl+C para detener el servicio.")
        print("=" * 60)

        # Ejecución inicial inmediata
        self.ejecutar_ronda()

        while not self.detenido:
            try:
                time.sleep(self.intervalo_segundos)
                self.ejecutar_ronda()
            except KeyboardInterrupt:
                print("\n[WORKER] Deteniendo servicio por solicitud del usuario...")
                self.detenido = True
                break
