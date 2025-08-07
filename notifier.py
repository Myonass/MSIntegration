import requests
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TG_TOKEN")

CHAT_ID = '1823753963'

def send_telegram_message(text):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {'chat_id': CHAT_ID, 'text': text}
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        print("✅ Сообщение успешно отправлено.")
    except Exception as e:
        print(f"❌ Ошибка при отправке в Telegram: {e}")

if __name__ == "__main__":
    send_telegram_message("Тестовое сообщение от Telegram-бота")
