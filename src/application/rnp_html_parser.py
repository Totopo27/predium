import re
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup
from src.domain.registro_models import (
    TitularFinca,
    TipoPersona,
    Gravamen,
    GravamenTipo,
    EstadoSociedad,
    DiagnosticoJuridicoFinca,
)
from src.application.diagnostico_patrimonial_service import DiagnosticoPatrimonialService


class RnpInformeParser:
    """
    Parser especializado en extraer datos jurídicos a partir del HTML de un
    Informe Registral de Bienes Inmuebles y Personas Jurídicas de rnpdigital.com.
    """

    def __init__(self, diagnostico_service: Optional[DiagnosticoPatrimonialService] = None):
        self.diagnostico_service = diagnostico_service or DiagnosticoPatrimonialService()

    def parsear_html_informe(self, html_contenido: str, folio_real: str) -> DiagnosticoJuridicoFinca:
        soup = BeautifulSoup(html_contenido, "lxml")
        texto_completo = soup.get_text(separator=" ", strip=True)

        titulares = self._extraer_titulares(soup, texto_completo)
        gravamenes = self._extraer_gravamenes(soup, texto_completo)
        estado_sociedad = self._detectar_estado_sociedad(titulares, texto_completo)

        return self.diagnostico_service.evaluar_finca(
            folio_real=folio_real,
            titulares=titulares,
            gravamenes=gravamenes,
            estado_sociedad=estado_sociedad,
        )

    def _extraer_titulares(self, soup: BeautifulSoup, texto: str) -> List[TitularFinca]:
        titulares: List[TitularFinca] = []

        # Buscar patrones de cédula jurídica (3-101-XXXXXX o 3101XXXXXX) o física (1-XXXX-XXXX)
        matches_juridicas = re.findall(
            r"(?:c[eé]dula|c[eé]dula jur[ií]dica)\s*[:\s]*([3-9]-?\d{3}-?\d{6})",
            texto,
            re.IGNORECASE,
        )
        for c in matches_juridicas:
            # Buscar nombre cercano o usar genérico
            c_norm = c.replace("-", "")
            nombre_m = re.search(rf"{re.escape(c)}[\s\-:,]+([A-Z0-9\s,\.]{{4,40}}?)(?:domicilio|derecho|citas|\.|$)", texto, re.IGNORECASE)
            nombre = nombre_m.group(1).strip() if nombre_m else "PERSONA JURIDICA REGISTRAL"
            titulares.append(
                TitularFinca(
                    nombre=nombre.upper(),
                    cedula=c,
                    tipo=TipoPersona.JURIDICA,
                )
            )

        matches_fisicas = re.findall(
            r"(?:c[eé]dula|identidad|identificaci[oó]n)\s*[:\s]*([1-7]-?\d{4}-?\d{4})",
            texto,
            re.IGNORECASE,
        )
        for c in matches_fisicas:
            nombre_m = re.search(rf"{re.escape(c)}[\s\-:,]+([A-Za-z\s]{{4,40}}?)(?:domicilio|derecho|citas|\.|$)", texto, re.IGNORECASE)
            nombre = nombre_m.group(1).strip() if nombre_m else "PROPIETARIO REGISTRAL"
            titulares.append(
                TitularFinca(
                    nombre=nombre.title(),
                    cedula=c,
                    tipo=TipoPersona.FISICA,
                )
            )

        if not titulares:
            titulares.append(
                TitularFinca(
                    nombre="PROPIETARIO REGISTRAL NO IDENTIFICADO",
                    cedula="N/A",
                    tipo=TipoPersona.FISICA,
                )
            )

        return titulares

    def _extraer_gravamenes(self, soup: BeautifulSoup, texto: str) -> List[Gravamen]:
        gravamenes: List[Gravamen] = []

        # Hipotecas
        matches_hipo = re.findall(
            r"hipoteca\s*(?:de\s+primer\s+grado|de\s+segundo\s+grado|[^\.\n]*?)\s*(?:a favor de\s+([A-Za-z0-9\s\.,]+?))?(?:por\s+la\s+suma\s+de\s*([₡$]?[\d\.,]+))?(?:citas\s*[:\s]*([0-9\-]+))?",
            texto,
            re.IGNORECASE,
        )
        for m in matches_hipo:
            acreedor = m[0].strip() if m[0] else None
            monto_str = m[1].replace(".", "").replace(",", ".").replace("₡", "").replace("$", "").strip() if m[1] else None
            monto = float(monto_str) if monto_str and monto_str.replace(".", "").isdigit() else None
            citas = m[2].strip() if len(m) > 2 and m[2] else None
            gravamenes.append(
                Gravamen(
                    tipo=GravamenTipo.HIPOTECA,
                    descripcion="Hipoteca registrada",
                    acreedor_o_beneficiario=acreedor,
                    monto=monto,
                    citas=citas,
                )
            )

        # Embargos y Demandas
        if re.search(r"\b(?:embargo\s+practicado|decretado\s+embargo|anotaci[oó]n\s+de\s+demanda)\b", texto, re.IGNORECASE):
            gravamenes.append(
                Gravamen(
                    tipo=GravamenTipo.EMBARGO,
                    descripcion="Embargo o demanda judicial anotada sobre la finca",
                )
            )

        # Usufructo
        if re.search(r"\b(?:usufructo\s+vitalicio|reserva\s+de\s+usufructo)\b", texto, re.IGNORECASE):
            gravamenes.append(
                Gravamen(
                    tipo=GravamenTipo.USUFRUCTO,
                    descripcion="Usufructo vitalicio constituido",
                )
            )

        # Bono de Vivienda
        if re.search(r"\b(?:bono\s+familiar\s+de\s+vivienda|ley\s+7052|banhvi)\b", texto, re.IGNORECASE):
            gravamenes.append(
                Gravamen(
                    tipo=GravamenTipo.BONO_VIVIENDA,
                    descripcion="Limitación por Bono Familiar de Vivienda (BANHVI)",
                )
            )

        return gravamenes

    def _detectar_estado_sociedad(self, titulares: List[TitularFinca], texto: str) -> EstadoSociedad:
        if re.search(r"\b(?:disuelta\s+por\s+ley\s+9428|sociedad\s+disuelta|disoluci[oó]n\s+por\s+morosidad)\b", texto, re.IGNORECASE):
            return EstadoSociedad.DISUELTA_POR_LEY_9428
        if re.search(r"\b(?:en\s+liquidaci[oó]n)\b", texto, re.IGNORECASE):
            return EstadoSociedad.EN_LIQUIDACION

        for t in titulares:
            if t.tipo == TipoPersona.JURIDICA:
                return EstadoSociedad.ACTIVA

        return EstadoSociedad.NO_APLICA
