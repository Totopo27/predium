import pytest
from src.application.rnp_html_parser import RnpInformeParser
from src.domain.registro_models import EstrategiaSaneamiento, TipoPersona


def test_parser_rnp_html_sociedad_disuelta():
    html_ficticio = """
    <html>
      <body>
        <div class="informe">
          <h1>REGISTRO INMOBILIARIO - MATRÍCULA: 2-120500-000</h1>
          <p>PROPIETARIO: Cédula Jurídica: 3-101-554433 INVERSIONES MONTE VERDE S.A. DERECHO: 1/1</p>
          <p>ESTADO DE LA PERSONA JURÍDICA: SOCIEDAD DISUELTA POR LEY 9428</p>
          <p>NATURALEZA: Terreno para agricultura y bosque</p>
          <p>PLANO: A-123456-2015 MEDIDA: 5000 METROS CUADRADOS</p>
          <p>GRAVÁMENES: Hipoteca de primer grado a favor de Banco de Costa Rica por la suma de ₡15.000.000 citas: 450-12345-01-0001-001</p>
        </div>
      </body>
    </html>
    """

    parser = RnpInformeParser()
    diag = parser.parsear_html_informe(html_ficticio, "2-120500-000")

    assert diag.folio_real == "2-120500-000"
    assert len(diag.titulares) >= 1
    assert diag.titulares[0].tipo == TipoPersona.JURIDICA
    assert diag.alerta_sociedad_disuelta is True
    assert diag.estrategia_sugerida == EstrategiaSaneamiento.LIQUIDACION_SOCIEDAD_DISUELTA


def test_parser_rnp_html_usufructo_y_adulto_mayor():
    html_ficticio = """
    <html>
      <body>
        <div>
          <h2>CONSULTA DE FINCA: 2-334455-000</h2>
          <p>TITULAR: Identificación: 2-0111-0333 DON MANUEL VARGAS ROJAS DERECHO: 1/1</p>
          <p>AFECTACIONES: Se encuentra constituido Usufructo Vitalicio a favor del señor Manuel Vargas Rojas</p>
          <p>PLANO: A-998877-2018 MEDIDA: 850.50 METROS CUADRADOS</p>
        </div>
      </body>
    </html>
    """

    parser = RnpInformeParser()
    diag = parser.parsear_html_informe(html_ficticio, "2-334455-000")

    assert diag.folio_real == "2-334455-000"
    assert diag.alerta_usufructo_activo is True
    assert diag.estrategia_sugerida == EstrategiaSaneamiento.NUDA_PROPIEDAD_USUFRUCTO


def test_parser_rnp_html_embargo_judicial():
    html_ficticio = """
    <html>
      <body>
        <div>
          <h2>MATRÍCULA: 2-998877-000</h2>
          <p>PROPIETARIO: Cédula 1-0555-0444 JUAN BAUTISTA SOTO</p>
          <p>GRAVÁMENES: Decretado embargo practicado por el Juzgado de Cobro de Alajuela en expediente 22-00123-CJ</p>
          <p>Hipoteca a favor de Cooperativa por la suma de ₡20.000.000</p>
        </div>
      </body>
    </html>
    """

    parser = RnpInformeParser()
    diag = parser.parsear_html_informe(html_ficticio, "2-998877-000")

    assert diag.alerta_embargos_judiciales is True
    assert diag.estrategia_sugerida == EstrategiaSaneamiento.COMPRA_PREVIA_REMATE
