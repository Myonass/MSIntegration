import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()  

login = os.getenv("MS_LOGIN")
password = os.getenv("MS_PASSWORD")

cred = base64.b64encode(f"{login}:{password}".encode()).decode()
headers = {
    'Authorization': f'Basic {cred}',
    'Accept-Encoding': 'gzip'
}
resp = requests.post('https://api.moysklad.ru/api/remap/1.2/security/token', headers=headers)
token = resp.json()['access_token']
print("Токен получен:", token)
