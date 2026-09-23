import pytest
from shapely.geometry import Polygon, box
from src.application.gap_detector import GapDetector


def test_deteccion_vacio_simple():
    detector = GapDetector()

    # Supongamos un distrito cuadrado de 100m x 100m = 10,000 m2
    distrito = box(0, 0, 100, 100)

    # Predio 1: de 0 a 40 (en X) y 0 a 100 (en Y) -> 40 x 100 = 4,000 m2
    predio_1 = box(0, 0, 40, 100)
    # Predio 2: de 60 a 100 (en X) y 0 a 100 (en Y) -> 40 x 100 = 4,000 m2
    predio_2 = box(60, 0, 100, 100)

    # Queda un hueco o vacío en el centro de X: 40 a 60, Y: 0 a 100 -> 20 x 100 = 2,000 m2
    predios = [
        {"finca": "111", "geometry": predio_1},
        {"finca": "222", "geometry": predio_2},
    ]

    resultado = detector.analizar_zona(
        distrito_nombre="Zarcero Centro",
        geometria_distrito=distrito,
        predios_catastrados=predios,
        area_minima_m2=100.0,
    )

    assert resultado.total_vacios_detectados == 1
    vacio = resultado.vacios[0]
    assert pytest.approx(vacio.area_estimada_m2, rel=1e-2) == 2000.0
    assert "111" in vacio.fincas_colindantes
    assert "222" in vacio.fincas_colindantes


def test_filtro_de_astillas_topologicas():
    detector = GapDetector()
    distrito = box(0, 0, 100, 100)

    # Predios casi contiguos con una pequeña astilla de 5 m2
    predio_1 = box(0, 0, 50, 100)
    predio_2 = box(50.1, 0, 100, 100)  # Brecha de 0.1m x 100m = 10 m2

    predios = [
        {"finca": "A", "geometry": predio_1},
        {"finca": "B", "geometry": predio_2},
    ]

    # Con umbral de 300 m2, la astilla debe ser descartada
    resultado = detector.analizar_zona(
        distrito_nombre="Laguna",
        geometria_distrito=distrito,
        predios_catastrados=predios,
        area_minima_m2=300.0,
    )

    assert resultado.total_vacios_detectados == 0
