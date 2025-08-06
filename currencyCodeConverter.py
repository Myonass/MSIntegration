import requests
from config import API_BASE_URL, HEADERS

def get_currency_code(currency_href):
    """
    Запрашивает валюту по ссылке и возвращает её код (например, 'EUR', 'RUB').
    """
    response = requests.get(currency_href, headers=HEADERS)
    if response.status_code != 200:
        print(f"Ошибка при получении валюты: {response.status_code}, ответ: {response.text}")
        return "UNKNOWN"
    data = response.json()
    for key in ("isoCode", "iso4217Code", "code", "name"):
        val = data.get(key)
        if val:
            # Если это числовой код (int), преобразуем в строку
            if isinstance(val, int):
                val = str(val)
            # Если val — строка, проверим, что она не число (если число, попробуем следующее)
            if not val.isdigit():
                return val
            elif key == "code":
                # Если это код и он числовой, сохраним его на случай
                numeric_code = val
    # Если не нашли буквенный код, вернём числовой код или UNKNOWN
    return numeric_code if 'numeric_code' in locals() else "UNKNOWN"
