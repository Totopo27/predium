import pytest
from src.application.boletin_parser import BoletinJudicialParser
from src.domain.models import Moneda


def test_parsear_edicto_zarcero_base():
    texto_ejemplo = """
    En este Despacho, con una base de cuarenta y cinco millones de colones exactos, libre de gravámenes hipotecarios; sáquese a remate la finca del partido de Alajuela, matrícula número 245123-000, la cual es terreno de agricultura. Situada en el distrito 01 Zarcero, cantón 11 Zarcero, de la provincia de Alajuela. Mide: mil doscientos cincuenta metros con cero decímetros cuadrados. Plano: A-1892341-2018. Para el segundo remate se señalan las trece horas treinta minutos del quince de noviembre de dos mil veinticuatro, con la base de treinta y tres millones setecientos cincuenta mil colones (75% de la base original), y para la tercera subasta se señalan las trece horas treinta minutos del treinta de noviembre de dos mil veinticuatro, con la base de once millones doscientos cincuenta mil colones (25% de la base original). Se remata por ordenarse así en proceso ejecución hipotecaria de Banco Nacional de Costa Rica contra Inversiones Las Brisas S.A., expediente 23-001234-1200-CJ. ( IN2024987654 ).
    """
    
    parser = BoletinJudicialParser()
    edicto = parser.parsear_texto_edicto(texto_ejemplo)

    assert edicto is not None
    assert edicto.id_edicto == "IN2024987654"
    assert edicto.finca.provincia_codigo == 2  # Alajuela
    assert edicto.finca.numero_finca == "245123"
    assert edicto.finca.derecho == "000"
    assert edicto.finca.folio_real == "2-245123-000"
    assert edicto.finca.plano_catastrado == "A-1892341-2018"
    assert edicto.ubicacion.provincia.lower() == "alajuela"
    assert "zarcero" in edicto.ubicacion.canton.lower()
    assert edicto.expediente == "23-001234-1200-CJ"
    assert "Banco Nacional de Costa Rica" in edicto.acreedor
    assert "Inversiones Las Brisas" in edicto.demandado
    assert edicto.base.moneda == Moneda.CRC


def test_filtro_por_canton_zarcero():
    parser = BoletinJudicialParser()
    texto_zarcero = "situada en el cantón Zarcero, provincia de Alajuela. Matrícula 2-123456-000. Base: diez millones de colones. ( IN2024111111 )."
    texto_san_jose = "situada en el cantón Desamparados, provincia de San José. Matrícula 1-654321-000. Base: veinte millones de colones. ( IN2024222222 )."
    
    assert parser.es_de_canton(texto_zarcero, "Zarcero") is True
    assert parser.es_de_canton(texto_zarcero, "Alfaro Ruiz") is True  # Sinónimo histórico
    assert parser.es_de_canton(texto_san_jose, "Zarcero") is False
