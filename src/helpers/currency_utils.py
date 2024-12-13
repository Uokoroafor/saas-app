def get_currency_symbol(currency_code: str) -> str:
    """
    Retrieve the symbol for a given currency code.

    This function takes a currency code as input and returns the corresponding
    currency symbol. If the provided currency code is not found, it returns
    "Unknown Currency Code".

    Args:
        currency_code (str): The three-letter ISO 4217 currency code (e.g., "USD", "EUR").

    Returns:
        str: The currency symbol corresponding to the provided currency code.
        If the currency code is not recognized, returns "Unknown Currency Code".

    Examples:
        >>> get_currency_symbol("USD")
        '$'
        >>> get_currency_symbol("eur")
        '€'
        >>> get_currency_symbol("XYZ")
        'Unknown Currency Code'
    """
    currency_symbols = {
        "USD": "$",  # US Dollar
        "EUR": "€",  # Euro
        "GBP": "£",  # British Pound
        "JPY": "¥",  # Japanese Yen
        "AUD": "A$",  # Australian Dollar
        "CAD": "C$",  # Canadian Dollar
        "CHF": "CHF",  # Swiss Franc
        "CNY": "¥",  # Chinese Yuan
        "SEK": "kr",  # Swedish Krona
        "NZD": "NZ$",  # New Zealand Dollar
        "INR": "₹",  # Indian Rupee
        "RUB": "₽",  # Russian Ruble
        "ZAR": "R",  # South African Rand
        "BRL": "R$",  # Brazilian Real
        "MXN": "$",  # Mexican Peso
        "SGD": "S$",  # Singapore Dollar
        "HKD": "HK$",  # Hong Kong Dollar
        "NOK": "kr",  # Norwegian Krone
        "KRW": "₩",  # South Korean Won
        "TRY": "₺",  # Turkish Lira
        "ARS": "$",  # Argentine Peso
        "PLN": "zł",  # Polish Zloty
    }

    return currency_symbols.get(currency_code.upper(), "Unk")
