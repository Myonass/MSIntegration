import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN_MS")

API_BASE_URL = "https://api.moysklad.ru/api/remap/1.2"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept-Encoding": "gzip",
    "Content-Type": "application/json"
}
