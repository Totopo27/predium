import re
from typing import Optional

UNIDADES = {
    "cero": 0, "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4,
    "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
    "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15,
    "dieciseis": 16, "diecisiete": 17, "dieciocho": 18, "diecinueve": 19,
    "veinte": 20, "veintiuno": 21, "veintidos": 22, "veintitres": 23,
    "veinticuatro": 24, "veinticinco": 25, "veintiseis": 26, "veintisiete": 27,
    "veintiocho": 28, "veintinueve": 29, "treinta": 30, "cuarenta": 40,
    "cincuenta": 50, "sesenta": 60, "setenta": 70, "ochenta": 80, "noventa": 90,
}

CENTENAS = {
    "cien": 100, "ciento": 100, "doscientos": 200, "trescientos": 300,
    "cuatrocientos": 400, "quinientos": 500, "seiscientos": 600,
    "setecientos": 700, "ochocientos": 800, "novecientos": 900,
}


def palabras_a_numero(texto: str) -> Optional[float]:
    """
    Convierte una expresión numérica en español a float.
    Ej: 'cuarenta y cinco millones de colones' -> 45000000.0
    """
    texto_limpio = texto.lower().replace(" y ", " ")
    tokens = re.findall(r"[a-z0-9\.,]+", texto_limpio)
    
    total = 0.0
    actual = 0.0
    encontrado = False

    for token in tokens:
        # Si es un número explícito en dígitos
        if re.match(r"^\d+(?:[\.,]\d+)?$", token):
            num = float(token.replace(".", "").replace(",", "."))
            actual += num
            encontrado = True
        elif token in UNIDADES:
            actual += UNIDADES[token]
            encontrado = True
        elif token in CENTENAS:
            actual += CENTENAS[token]
            encontrado = True
        elif token == "mil":
            actual = max(1.0, actual) * 1000.0
            total += actual
            actual = 0.0
            encontrado = True
        elif token in ("millon", "millones"):
            actual = max(1.0, actual) * 1000000.0
            total += actual
            actual = 0.0
            encontrado = True

    total += actual
    return total if encontrado else None
