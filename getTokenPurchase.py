# getTokenPurchase.py
import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

def get_token_purchase():
    """
    Возвращает заголовки с Basic Auth для заказов поставщикам
    """
    login = os.getenv("MS_LOGIN")
    password = os.getenv("MS_PASSWORD")

    auth_header = base64.b64encode(f"{login}:{password}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/json",
        "Accept-Encoding": "gzip"
    }
    return headers
