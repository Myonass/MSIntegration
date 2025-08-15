import requests
import os
from dotenv import load_dotenv

load_dotenv()

login = os.getenv("MS_LOGIN")
password = os.getenv("MS_PASSWORD")

url_token = "https://api.moysklad.ru/api/remap/1.2/security/token"
data = {
    "grant_type": "password",
    "username": login,
    "password": password
}

resp = requests.post(url_token, data=data)
resp.raise_for_status()
token = resp.json()['access_token']
print("Токен получен:", token)

# Дальнейший запрос с токеном
headers = {"Authorization": f"Bearer {token}"}
url_orders = "https://api.moysklad.ru/api/remap/1.2/entity/customerorder?offset=0&limit=100"
resp_orders = requests.get(url_orders, headers=headers)
resp_orders.raise_for_status()
orders = resp_orders.json()
print(orders)
