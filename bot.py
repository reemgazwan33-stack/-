import os
import requests
from flask import Flask, request

BOT_TOKEN = os.environ["BOT_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

MODEL = "gemini-2.5-flash"

WEBHOOK_URL = "https://telegram-ai-bot-335e.onrender.com/telegram-webhook"

app = Flask(__name__)


SYSTEM_PROMPT = """
أنت مساعد شخصي للرد على رسائل Telegram.

قواعدك:
- اكتب بالعربية بشكل أساسي.
- استخدم لهجة سعودية خفيفة وطبيعية.
- كن لطيفًا ومختصرًا.
- افهم الرسالة وأجب مباشرة.
- إذا كانت تحية، رد بتحية لطيفة.
- لا تخترع معلومات أو أسعار أو مواعيد.
- لا تكشف كلمات المرور أو الرموز أو أي بيانات خاصة.
- إذا احتاج الموضوع صاحب الحساب، قل إن صاحب الحساب سيرد لاحقًا.
- لا تذكر أنك ذكاء اصطناعي إلا إذا سُئلت مباشرة.
"""


def telegram(method, data=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"

    response = requests.post(
        url,
        json=data or {},
        timeout=30
    )

    return response.json()


def get_ai_reply(text):
    url = (
        f"https://generativelanguage.googleapis.com/"
        f"v1beta/models/{MODEL}:generateContent"
        f"?key={GEMINI_API_KEY}"
    )

    data = {
        "system_instruction": {
            "parts": [
                {
                    "text": SYSTEM_PROMPT
                }
            ]
        },
        "contents": [
            {
                "parts": [
                    {
                        "text": text
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 300
        }
    }

    response = requests.post(
        url,
        json=data,
        timeout=60
    )

    result = response.json()

    try:
        return result["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        print("GEMINI ERROR:", result, flush=True)
        return "أحتاج أتأكد من الموضوع وأرجع لك."


@app.get("/")
def home():
    return "Telegram AI Bot is running."


@app.get("/status")
def status():
    return telegram("getWebhookInfo")


@app.get("/setup")
def setup():
    try:
        result = telegram(
            "setWebhook",
            {
                "url": WEBHOOK_URL,
                "allowed_updates": [
                    "message",
                    "business_message"
                ],
                "drop_pending_updates": False
            }
        )

        return result

    except Exception as e:
        return {
            "error": str(e)
        }, 500


@app.post("/telegram-webhook")
def telegram_webhook():

    update = request.get_json(silent=True) or {}

    print("UPDATE RECEIVED:", update, flush=True)

    # =========================
    # رسائل البوت العادية
    # =========================

    message = update.get("message")

    if message:

        chat_id = message.get("chat", {}).get("id")
        text = (message.get("text") or "").strip()

        if not chat_id:
            return "ok", 200

        if text.startswith("/start"):
            reply = (
                "هلا 👋\n\n"
                "أنا بوت إدارة المحادثات 🤖\n"
                "وأقدر أساعد في الرد على الرسائل.\n\n"
                "الأوامر المتاحة:\n"
                "/start - تشغيل البوت\n"
                "/help - المساعدة\n"
                "/status - حالة البوت"
            )

        elif text.startswith("/help"):
            reply = (
                "الأوامر المتاحة 🤖\n\n"
                "/start - تشغيل البوت\n"
                "/help - عرض المساعدة\n"
                "/status - معرفة حالة البوت"
            )

        elif text.startswith("/status"):
            reply = "البوت شغال تمام ✅"

        elif text:
            reply = get_ai_reply(text)

        else:
            return "ok", 200

        telegram(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": reply
            }
        )

        return "ok", 200


    # =========================
    # رسائل Telegram Business
    # =========================

    business_message = update.get("business_message")

    if business_message:

        text = (business_message.get("text") or "").strip()

        business_connection_id = business_message.get(
            "business_connection_id"
        )

        chat_id = business_message.get(
            "chat", {}
        ).get("id")

        if not text:
            return "ok", 200

        if not business_connection_id:
            print(
                "No business_connection_id",
                flush=True
            )
            return "ok", 200

        if chat_id is None:
            print(
                "No chat_id",
                flush=True
            )
            return "ok", 200

        print(
            "BUSINESS MESSAGE:",
            text,
            flush=True
        )

        try:

            reply = get_ai_reply(text)

            print(
                "AI REPLY:",
                reply,
                flush=True
            )

            telegram(
                "sendMessage",
                {
                    "business_connection_id":
                        business_connection_id,
                    "chat_id": chat_id,
                    "text": reply
                }
            )

            print(
                "BUSINESS REPLY SENT",
                flush=True
            )

        except Exception as e:

            print(
                "BUSINESS REPLY ERROR:",
                e,
                flush=True
            )

        return "ok", 200


    return "ok", 200
