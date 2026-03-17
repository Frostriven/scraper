import unicodedata
import re

MEDICINA_KEYWORDS = [
    "medic", "cirujano", "cirujana", "ginec", "pediatr",
    "psiquiat", "cardiol", "neurolog", "oncolog", "dermatol",
    "oftalmol", "ortoped", "urolog", "gastroenterol", "neumol",
    "endocrinol", "reumatol", "infectolog", "anestesiol",
    "radiolog", "patolog", "medico", "médico", "médica",
    "urgencias", "familiar", "general", "interna", "internista",
    "traumatol", "hematolg", "nefrol", "hepatol",
]


def es_medicina(titulo: str) -> bool:
    titulo_lower = titulo.lower()
    return any(k in titulo_lower for k in MEDICINA_KEYWORDS)


def limpiar_texto(texto: str | None) -> str:
    if not texto:
        return ""
    return re.sub(r"\s+", " ", texto).strip().upper()
