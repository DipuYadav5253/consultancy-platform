import zlib

from django import template

register = template.Library()

SYMBOLS = {"GBP": "£", "USD": "$", "CAD": "C$", "AUD": "A$", "EUR": "€", "NZD": "NZ$"}

# The main destinations get fixed, distinct colours; any other country gets a stable one.
FIXED_TONES = {"GB": 3, "CA": 2, "AU": 1, "US": 6, "IE": 4, "DE": 5}


@register.filter
def money(value, currency):
    """18000 + 'GBP' -> '£18,000'. Unknown currencies show their code."""
    if value is None:
        return ""
    symbol = SYMBOLS.get(currency, f"{currency} ")
    return f"{symbol}{value:,.0f}"


@register.filter
def tone(code):
    """Colour theme (1 to 6) for a country card; always the same for the same country."""
    code = str(code).upper()
    return FIXED_TONES.get(code) or zlib.crc32(code.encode()) % 6 + 1
