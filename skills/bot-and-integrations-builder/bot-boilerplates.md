# Bot Boilerplates

## Lightweight Telegram Bot (No Heavy Dependencies)
```python
import os
import time
import requests

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
API_URL = f"https://api.telegram.org/bot{TOKEN}"

def get_updates(offset=None):
    params = {"timeout": 30, "offset": offset}
    try:
        resp = requests.get(f"{API_URL}/getUpdates", params=params, timeout=35)
        return resp.json().get("result", [])
    except Exception as e:
        print(f"Error fetching updates: {e}")
        return []

def send_message(chat_id, text):
    requests.post(f"{API_URL}/sendMessage", json={"chat_id": chat_id, "text": text})
```
