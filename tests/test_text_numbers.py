from src.application.text_numbers import palabras_a_numero


def test_palabras_a_numero_millones():
    assert palabras_a_numero("cuarenta y cinco millones") == 45_000_000.0
    assert palabras_a_numero("tres millones quinientos mil") == 3_500_000.0
    assert palabras_a_numero("un millon") == 1_000_000.0


def test_palabras_a_numero_digitos_y_texto():
    assert palabras_a_numero("base de 25000000 colones") == 25_000_000.0
    assert palabras_a_numero("15 mil dolares") == 15_000.0
