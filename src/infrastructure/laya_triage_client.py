import time
import re
from typing import Optional, Dict, Any
from src.domain.triage_models import (
    ResultadoTriageAvanzado,
    TipoBienClasificado,
    OrigenDeudaClasificado,
    UrgenciaSubasta,
    TipoOportunidadNegocio,
    ViabilidadSaneamiento,
)


class LayaTriageClient:
    """
    Motor de Decisiones de Sistema 1 basado en Laya (ModernBERT / mmBERT)
    configurado para evaluar oportunidades inmobiliarias de Costa Rica.
    """

    def __init__(self, usar_modelo_local: bool = True):
        self.usar_modelo_local = usar_modelo_local
        self.agent = None

        if self.usar_modelo_local:
            try:
                import laya
                self.agent = laya.load("convaiinnovations/laya", subfolder="multilingual")
            except Exception:
                self.agent = None

    def clasificar_inmueble(
        self,
        texto: str,
        precio_actual: Optional[float] = None,
        precio_original: Optional[float] = None,
        porcentaje_descuento: float = 0.0,
        no_georreferenciada_wfs: bool = False,
    ) -> ResultadoTriageAvanzado:
        """
        Evalúa un inmueble en 6 dimensiones estratégicas usando el modelo de Sistema 1,
        identificando candidatas a saneamiento si no existen en el mapa WFS digital.
        """
        t0 = time.perf_counter()

        if self.agent:
            return self._clasificar_con_laya(texto, t0, precio_actual, precio_original, porcentaje_descuento, no_georreferenciada_wfs)

        return self._clasificar_heuristico(texto, t0, precio_actual, precio_original, porcentaje_descuento, no_georreferenciada_wfs)

    def clasificar_edicto(self, texto_edicto: str) -> ResultadoTriageAvanzado:
        return self.clasificar_inmueble(texto_edicto)

    def _clasificar_con_laya(
        self,
        texto: str,
        t0: float,
        precio_actual: Optional[float] = None,
        precio_original: Optional[float] = None,
        porcentaje_descuento: float = 0.0,
        no_georreferenciada_wfs: bool = False,
    ) -> ResultadoTriageAvanzado:
        questions = {
            "tipo_bien": {
                "type": "choice",
                "instructions": "¿Qué tipo de bien se subasta o vende en este texto?",
                "criteria": {
                    "inmueble": "Finca, terreno, lote, casa, propiedad, apartamento, matrícula folio real, plano",
                    "vehiculo": "Automóvil, camión, moto, vehículo, placas, chasis, motor",
                    "mueble_otro": "Maquinaria, menaje, prendas, ganado, otros bienes muebles",
                },
            },
            "origen_deuda": {
                "type": "choice",
                "instructions": "¿Quién es el acreedor o qué origen tiene el proceso?",
                "criteria": {
                    "municipal": "Municipalidad, cobro municipal, tasas de basura, impuesto de bienes inmuebles",
                    "bancario": "Banco Nacional, Banco de Costa Rica, Banco Popular, BAC, mutual, cooperativa, financiera",
                    "particular": "Persona física, acreedor particular, empresa comercial privada",
                },
            },
            "tipo_oportunidad": {
                "type": "choice",
                "instructions": "¿Cuál es la tipología de oportunidad de negocio patrimonial que presenta este bien?",
                "criteria": {
                    "abandono_fiscal": "Deuda o remate municipal por impuestos no pagados",
                    "finca_no_georreferenciada": "Inmueble con título o plano antiguo sin incorporación al catastro digital",
                    "liquidacion_bancaria": "Bien adjudicado en venta por banco con descuento o financiamiento",
                    "vulnerabilidad_patrimonial": "Presencia de usufructo vitalicio, persona adulta mayor o proceso sucesorio",
                    "litigio_complejo": "Múltiples embargos, demandas judiciales o tercerías en trámite",
                    "estandar": "Proceso ordinario sin complejidades aparentes",
                },
            },
            "riesgo_bloqueante": {
                "type": "noul",
                "instructions": "¿Presenta afectaciones severas como bono de vivienda BANHVI, patrimonio familiar o usufructo?",
            },
            "urgencia": {
                "type": "choice",
                "instructions": "¿En qué etapa procesal se encuentra la venta o remate?",
                "criteria": {
                    "primera": "Primer remate, base 100%",
                    "segunda": "Segundo remate, base rebajada al 75%",
                    "tercera": "Tercera subasta, al 25% de la base original",
                    "venta_directa": "Bienes adjudicados en venta directa o concurso por entidad bancaria",
                },
            },
        }

        res = self.agent.predict({"texto": texto}, questions)
        answers = res.get("answers", {})

        tipo_str = answers.get("tipo_bien", {}).get("choice", "inmueble").upper()
        conf_tipo = answers.get("tipo_bien", {}).get("confidence", 0.92)

        origen_str = answers.get("origen_deuda", {}).get("choice", "bancario").upper()
        conf_origen = answers.get("origen_deuda", {}).get("confidence", 0.88)

        oportunidad_str = answers.get("tipo_oportunidad", {}).get("choice", "estandar").upper()
        if no_georreferenciada_wfs and oportunidad_str == "ESTANDAR":
            oportunidad_str = "FINCA_NO_GEORREFERENCIADA"

        prob_bloqueo = float(answers.get("riesgo_bloqueante", {}).get("noul", 0.1))
        tiene_bloqueo = prob_bloqueo > 0.55

        urgencia_str = answers.get("urgencia", {}).get("choice", "primera").upper()

        # Determinar viabilidad de saneamiento
        if tiene_bloqueo and ("bono" in texto.lower() or "banhvi" in texto.lower()):
            viabilidad = ViabilidadSaneamiento.BAJA
            detalles_bloqueo = "Gravamen por Bono Familiar de Vivienda (BANHVI Ley 7052)"
        elif no_georreferenciada_wfs:
            viabilidad = ViabilidadSaneamiento.MEDIA
            detalles_bloqueo = "Propiedad invisible en WFS municipal: requiere agrimensura y actualización cartográfica de linderos"
        elif tiene_bloqueo or oportunidad_str == "VULNERABILIDAD_PATRIMONIAL":
            viabilidad = ViabilidadSaneamiento.MEDIA
            detalles_bloqueo = "Requiere estructuración de Nuda Propiedad o trámite notarial de liquidación"
        else:
            viabilidad = ViabilidadSaneamiento.ALTA
            detalles_bloqueo = None

        # Calcular Score de Inversión (1 a 5)
        score = 3
        if oportunidad_str in ("ABANDONO_FISCAL", "FINCA_NO_GEORREFERENCIADA"):
            score += 1
        if urgencia_str == "TERCERA" or porcentaje_descuento >= 40.0:
            score += 1
        if viabilidad == ViabilidadSaneamiento.BAJA:
            score -= 2
        score = max(1, min(5, score))

        tiempo_ms = (time.perf_counter() - t0) * 1000.0

        return ResultadoTriageAvanzado(
            tipo_bien=TipoBienClasificado[tipo_str] if tipo_str in TipoBienClasificado.__members__ else TipoBienClasificado.INMUEBLE,
            confianza_tipo_bien=float(conf_tipo),
            es_inmueble=tipo_str == "INMUEBLE",
            origen_deuda=OrigenDeudaClasificado[origen_str] if origen_str in OrigenDeudaClasificado.__members__ else OrigenDeudaClasificado.BANCARIO,
            confianza_origen=float(conf_origen),
            es_morosidad_municipal=origen_str == "MUNICIPAL",
            tipo_oportunidad=TipoOportunidadNegocio[oportunidad_str] if oportunidad_str in TipoOportunidadNegocio.__members__ else TipoOportunidadNegocio.ESTANDAR,
            es_candidata_saneamiento=no_georreferenciada_wfs,
            probabilidad_saneamiento_exitoso=0.88 if no_georreferenciada_wfs else 0.70,
            viabilidad_saneamiento=viabilidad,
            tiene_gravamen_bloqueante=tiene_bloqueo or no_georreferenciada_wfs,
            probabilidad_bloqueo=prob_bloqueo,
            detalles_bloqueo=detalles_bloqueo,
            urgencia=UrgenciaSubasta[urgencia_str] if urgencia_str in UrgenciaSubasta.__members__ else UrgenciaSubasta.PRIMERA,
            score_inversion=score,
            tiempo_inferencia_ms=round(tiempo_ms, 2),
        )

    def _clasificar_heuristico(
        self,
        texto: str,
        t0: float,
        precio_actual: Optional[float] = None,
        precio_original: Optional[float] = None,
        porcentaje_descuento: float = 0.0,
        no_georreferenciada_wfs: bool = False,
    ) -> ResultadoTriageAvanzado:
        texto_lower = texto.lower()

        # 1. Tipo de bien
        if re.search(r"\b(?:veh[ií]culo|placas?|chasis|motor|marca\s+[A-Za-z]+|estilo\s+[A-Za-z]+)\b", texto_lower) and not re.search(r"\b(?:finca|matr[ií]cula|plano|terreno|lote)\b", texto_lower):
            tipo = TipoBienClasificado.VEHICULO
            conf_tipo = 0.95
        elif re.search(r"\b(?:maquinaria|mobiliario|prendari[ao])\b", texto_lower) and not re.search(r"\b(?:finca|terreno|lote)\b", texto_lower):
            tipo = TipoBienClasificado.MUEBLE_OTRO
            conf_tipo = 0.88
        else:
            tipo = TipoBienClasificado.INMUEBLE
            conf_tipo = 0.96

        # 2. Origen del crédito
        if re.search(r"\b(?:municipalidad|impuesto\s+de\s+bienes\s+inmuebles|tasas?\s+municipales?)\b", texto_lower):
            origen = OrigenDeudaClasificado.MUNICIPAL
            conf_origen = 0.94
        elif re.search(r"\b(?:banco|cooperativa|financiera|mutual|fideicomiso|bcr|bncr|bac)\b", texto_lower):
            origen = OrigenDeudaClasificado.BANCARIO
            conf_origen = 0.92
        else:
            origen = OrigenDeudaClasificado.PARTICULAR
            conf_origen = 0.75

        # 3. Oportunidad de Negocio
        if no_georreferenciada_wfs:
            oportunidad = TipoOportunidadNegocio.FINCA_NO_GEORREFERENCIADA
        elif origen == OrigenDeudaClasificado.MUNICIPAL:
            oportunidad = TipoOportunidadNegocio.ABANDONO_FISCAL
        elif "descuento" in texto_lower or "adjudicado" in texto_lower or porcentaje_descuento > 0:
            oportunidad = TipoOportunidadNegocio.LIQUIDACION_BANCARIA
        elif "usufructo" in texto_lower or "adulto mayor" in texto_lower or "sucesorio" in texto_lower:
            oportunidad = TipoOportunidadNegocio.VULNERABILIDAD_PATRIMONIAL
        elif "demanda" in texto_lower or "tercería" in texto_lower:
            oportunidad = TipoOportunidadNegocio.LITIGIO_COMPLEJO
        else:
            oportunidad = TipoOportunidadNegocio.ESTANDAR

        # 4. Riesgos bloqueantes
        tiene_banhvi = bool(re.search(r"\b(?:bono|banhvi|ley\s*7052)\b", texto_lower))
        tiene_usufructo = "usufructo" in texto_lower
        tiene_bloqueo = tiene_banhvi or tiene_usufructo or no_georreferenciada_wfs

        if tiene_banhvi:
            viabilidad = ViabilidadSaneamiento.BAJA
            detalles_bloqueo = "Afectación por Bono Familiar de Vivienda (BANHVI Ley 7052)"
            prob_bloqueo = 0.92
        elif no_georreferenciada_wfs:
            viabilidad = ViabilidadSaneamiento.MEDIA
            detalles_bloqueo = "Finca no localizada en mapa digital WFS: requiere actualización de plano de agrimensura"
            prob_bloqueo = 0.75
        elif tiene_usufructo:
            viabilidad = ViabilidadSaneamiento.MEDIA
            detalles_bloqueo = "Requiere estructuración de Nuda Propiedad respetando derecho vitalicio"
            prob_bloqueo = 0.85
        else:
            viabilidad = ViabilidadSaneamiento.ALTA
            detalles_bloqueo = None
            prob_bloqueo = 0.08

        # 5. Urgencia y Score
        if "tercer remate" in texto_lower or "tercera subasta" in texto_lower:
            urgencia = UrgenciaSubasta.TERCERA
        elif "segundo remate" in texto_lower or "segunda subasta" in texto_lower:
            urgencia = UrgenciaSubasta.SEGUNDA
        elif "adjudicado" in texto_lower or "oferta" in texto_lower:
            urgencia = UrgenciaSubasta.VENTA_DIRECTA
        else:
            urgencia = UrgenciaSubasta.PRIMERA

        score = 3
        if oportunidad in (TipoOportunidadNegocio.ABANDONO_FISCAL, TipoOportunidadNegocio.FINCA_NO_GEORREFERENCIADA):
            score += 1
        if urgencia == UrgenciaSubasta.TERCERA or porcentaje_descuento >= 40.0:
            score += 1
        if viabilidad == ViabilidadSaneamiento.BAJA:
            score -= 2
        score = max(1, min(5, score))

        tiempo_ms = (time.perf_counter() - t0) * 1000.0

        return ResultadoTriageAvanzado(
            tipo_bien=tipo,
            confianza_tipo_bien=conf_tipo,
            es_inmueble=tipo == TipoBienClasificado.INMUEBLE,
            origen_deuda=origen,
            confianza_origen=conf_origen,
            es_morosidad_municipal=origen == OrigenDeudaClasificado.MUNICIPAL,
            tipo_oportunidad=oportunidad,
            es_candidata_saneamiento=no_georreferenciada_wfs,
            probabilidad_saneamiento_exitoso=0.88 if no_georreferenciada_wfs else 0.70,
            viabilidad_saneamiento=viabilidad,
            tiene_gravamen_bloqueante=tiene_bloqueo,
            probabilidad_bloqueo=prob_bloqueo,
            detalles_bloqueo=detalles_bloqueo,
            urgencia=urgencia,
            score_inversion=score,
            tiempo_inferencia_ms=round(tiempo_ms, 2),
        )
