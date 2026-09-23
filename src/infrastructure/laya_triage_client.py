import time
import re
from typing import Optional, Dict, Any
from src.domain.triage_models import (
    ResultadoTriage,
    TipoBienClasificado,
    OrigenDeudaClasificado,
    UrgenciaSubasta,
)


class LayaTriageClient:
    """
    Cliente de Sistema 1 basado en Laya (ModernBERT / mmBERT) para triage
    de edictos judiciales en un solo forward pass (<35ms).
    """

    def __init__(self, usar_modelo_local: bool = False):
        self.usar_modelo_local = usar_modelo_local
        self.router = None

        if self.usar_modelo_local:
            try:
                import laya
                from laya import Router
                self.router = Router(preload=True)
            except Exception:
                self.router = None

    def clasificar_edicto(self, texto_edicto: str) -> ResultadoTriage:
        t0 = time.perf_counter()

        if self.router:
            return self._clasificar_con_laya(texto_edicto, t0)

        # Fast Heuristic Fallback (garantiza ejecución inmediata y determinista)
        return self._clasificar_heuristico(texto_edicto, t0)

    def _clasificar_con_laya(self, texto: str, t0: float) -> ResultadoTriage:
        questions = {
            "tipo_bien": {
                "type": "choice",
                "instructions": "¿Qué tipo de bien se remata en este edicto?",
                "criteria": {
                    "inmueble": "Finca, terreno, lote, casa, propiedad, matrícula folio real, plano",
                    "vehiculo": "Automóvil, camión, moto, vehículo, placas, chasis, motor",
                    "mueble_otro": "Maquinaria, menaje, prendas, ganado, otros bienes muebles",
                },
            },
            "origen_deuda": {
                "type": "choice",
                "instructions": "¿Quién es el acreedor o qué origen tiene la deuda?",
                "criteria": {
                    "municipal": "Municipalidad, impuestos territoriales, tasas municipales",
                    "bancario": "Banco, cooperativa de ahorro y crédito, financiera, fideicomiso",
                    "particular": "Persona física, acreedor particular, empresa comercial",
                },
            },
            "riesgo_complejo": {
                "type": "noul",
                "instructions": "¿Presenta el edicto gravámenes complejos como usufructo vitalicio o demanda judicial?",
            },
            "urgencia": {
                "type": "choice",
                "instructions": "¿En qué etapa de subasta se encuentra el remate?",
                "criteria": {
                    "primera": "Primer remate, base 100%",
                    "segunda": "Segundo remate, base al 75%",
                    "tercera": "Tercera subasta, al 25% de la base original",
                },
            },
        }

        res = self.router.predict({"texto": texto}, questions)
        answers = res.get("answers", {})

        tipo_str = answers.get("tipo_bien", {}).get("choice", "inmueble").upper()
        conf_tipo = answers.get("tipo_bien", {}).get("confidence", 0.90)

        origen_str = answers.get("origen_deuda", {}).get("choice", "bancario").upper()
        conf_origen = answers.get("origen_deuda", {}).get("confidence", 0.85)

        riesgo_noul = answers.get("riesgo_complejo", {}).get("noul", 0.1)

        urgencia_str = answers.get("urgencia", {}).get("choice", "primera").upper()

        tiempo_ms = (time.perf_counter() - t0) * 1000.0

        return ResultadoTriage(
            tipo_bien=TipoBienClasificado[tipo_str] if tipo_str in TipoBienClasificado.__members__ else TipoBienClasificado.INMUEBLE,
            confianza_tipo_bien=float(conf_tipo),
            origen_deuda=OrigenDeudaClasificado[origen_str] if origen_str in OrigenDeudaClasificado.__members__ else OrigenDeudaClasificado.BANCARIO,
            confianza_origen=float(conf_origen),
            es_inmueble=tipo_str == "INMUEBLE",
            es_morosidad_municipal=origen_str == "MUNICIPAL",
            riesgo_gravamen_complejo=riesgo_noul > 0.5,
            probabilidad_riesgo=float(riesgo_noul),
            urgencia=UrgenciaSubasta[urgencia_str] if urgencia_str in UrgenciaSubasta.__members__ else UrgenciaSubasta.PRIMERA,
            tiempo_inferencia_ms=round(tiempo_ms, 2),
        )

    def _clasificar_heuristico(self, texto: str, t0: float) -> ResultadoTriage:
        texto_lower = texto.lower()

        # Tipo de bien
        if re.search(r"\b(?:veh[ií]culo|placas?|chasis|motor|marca\s+[A-Za-z]+|estilo\s+[A-Za-z]+)\b", texto_lower) and not re.search(r"\b(?:finca|matr[ií]cula|plano)\b", texto_lower):
            tipo = TipoBienClasificado.VEHICULO
            conf_tipo = 0.95
        elif re.search(r"\b(?:maquinaria|mobiliario|prendari[ao])\b", texto_lower) and not re.search(r"\b(?:finca|terreno)\b", texto_lower):
            tipo = TipoBienClasificado.MUEBLE_OTRO
            conf_tipo = 0.88
        else:
            tipo = TipoBienClasificado.INMUEBLE
            conf_tipo = 0.96

        # Origen de la deuda
        if re.search(r"\b(?:municipalidad|impuesto\s+de\s+bienes\s+inmuebles|tasas?\s+municipales?)\b", texto_lower):
            origen = OrigenDeudaClasificado.MUNICIPAL
            conf_origen = 0.94
        elif re.search(r"\b(?:banco|cooperativa|financiera|mutual|fideicomiso)\b", texto_lower):
            origen = OrigenDeudaClasificado.BANCARIO
            conf_origen = 0.92
        else:
            origen = OrigenDeudaClasificado.PARTICULAR
            conf_origen = 0.75

        # Riesgo complejo
        tiene_riesgo = bool(re.search(r"\b(?:usufructo|anotaci[oó]n\s+de\s+demanda|patrimonio\s+familiar|concesi[oó]n)\b", texto_lower))
        prob_riesgo = 0.89 if tiene_riesgo else 0.08

        # Urgencia
        if "tercer remate" in texto_lower or "tercera subasta" in texto_lower:
            urgencia = UrgenciaSubasta.TERCERA
        elif "segundo remate" in texto_lower or "segunda subasta" in texto_lower:
            urgencia = UrgenciaSubasta.SEGUNDA
        else:
            urgencia = UrgenciaSubasta.PRIMERA

        tiempo_ms = (time.perf_counter() - t0) * 1000.0

        return ResultadoTriage(
            tipo_bien=tipo,
            confianza_tipo_bien=conf_tipo,
            origen_deuda=origen,
            confianza_origen=conf_origen,
            es_inmueble=tipo == TipoBienClasificado.INMUEBLE,
            es_morosidad_municipal=origen == OrigenDeudaClasificado.MUNICIPAL,
            riesgo_gravamen_complejo=tiene_riesgo,
            probabilidad_riesgo=prob_riesgo,
            urgencia=urgencia,
            tiempo_inferencia_ms=round(tiempo_ms, 2),
        )
