import os
import time
import json
import threading
import requests
from flask import Flask
from google import genai
from google.genai import types

BOT_TOKEN = os.environ["BOT_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

client = genai.Client(api_key=GEMINI_API_KEY)

app = Flask(__name__)

SYSTEM_PROMPT = """
أنت مساعد شخصي للرد على رسائل Telegram.
رد بالعربية بشكل طبيعي وودود، مع لهجة سعودية خفيفة.
اجعل الرد مختصرًا وواضحًا.
لا تذكر أنك روبوت أو ذكاء اصطناعي إلا إذا سُئلت مباشرة.
لا تخترع معلومات.
إذا لم تعرف الإجابة، قل إنك تحتاج للتأكد.
إذا كانت الرسالة تحية، رد بتحية لطيفة.
استخدم الإيموجي باعتدال.
"""

@app.get("/")
def home():
    return "Bot is running"

def get_ai_reply(message):
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=message,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.7,
            max_output_tokens=300
        )
    )
    return (response.text or "").strip()

def telegram(method, data=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    response = requests.post(url, json=data or {}, timeout=60)
    return response.json()

def run_bot():
    telegram("deleteWebhook", {"drop_pending_updates": False})

    offset = 0

    while True:
        try:
            response = requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
                params={
                    "offset": offset,
                    "timeout": 50,
    
                },
                timeout=60
            )

            updates = response.json().get("result", [])

            for update in updates:
                offset = update["update_id"] + 1

                message = update.get("business_message")
                if not message:
                    continue

                text = message.get("text")
                business_connection_id = message.get("business_connection_id")
                chat_id = message.get("chat", {}).get("id")

                if not text or not business_connection_id or not chat_id:
                    continue

                try:
                    reply = get_ai_reply(text)

                    if reply:
                        telegram(
                            "sendMessage",
                            {
                                "business_connection_id": business_connection_id,
                                "chat_id": chat_id,
                                "text": reply
                            }
                        )

                except Exception as e:
                    print("Reply error:", e)

        except Exception as e:
            print("Bot error:", e)
            time.sleep(5)

threading.Thread(target=run_bot, daemon=True).start()
