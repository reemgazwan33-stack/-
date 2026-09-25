import os
import requests
from flask import Flask, request
from google import genai
from google.genai import types

BOT_TOKEN = os.environ["BOT_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

MODEL = "gemini-3.8-flash"

WEBHOOK_URL = "https://telegram-ai-bot-335e.onrender.com/telegram-webhook"

app = Flask(__name__)

client = genai.Client(api_key=GEMINI_API_KEY)


SYSTEM_PROMPT = """
أنت مساعد شخصي للرد على رسائل Telegram.

مهمتك الرد على الأشخاص الذين يرسلون رسائل إلى الحساب بطريقة طبيعية ودودة ومحترمة.

القواعد:
- اكتب بالعربية بشكل أساسي.
- استخدم اللهجة السعودية بشكل خفيف وطبيعي.
- اجعل الرد مختصرًا وواضحًا.
- افهم سؤال الشخص ثم أجب مباشرة.
- لا تذكر أنك روبوت أو ذكاء اصطناعي إلا إذا سُئلت مباشرة.
- لا تخترع معلومات أو مواعيد أو أسعار أو وعود.
- إذا لم تعرف الإجابة، قل إنك تحتاج للتأكد.
- لا ترسل رسائل كثيرة متتالية.
- كن لطيفًا وطبيعيًا.
- استخدم الإيموجي باعتدال 😊
- إذا كانت الرسالة تحية، رد بتحية لطيفة.
- إذا كانت الرسالة غير واضحة، اطلب توضيحًا بسيطًا.
- لا تكشف أي معلومات خاصة أو كلمات مرور أو رموز أو بيانات حساسة.
- إذا احتاج الموضوع تدخل صاحب الحساب، قل إن صاحب الحساب سيرد عليه لاحقًا.
"""


def telegram(method, data=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"

    response = requests.post(
        url,
        json=data or {},
        timeout=60
    )

    result = response.json()

    if not result.get("ok"):
        raise Exception(result)

    return result


def get_ai_reply(text):
    response = client.models.generate_content(
        model=MODEL,
        contents=text,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.7,
            max_output_tokens=300
        )
    )

    reply = (response.text or "").strip()

    if not reply:
        return "أحتاج أتأكد من الموضوع وأرجع لك 😊"

    return reply


@app.get("/")
def home():
    return "Telegram AI Bot is running."


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
        return {"error": str(e)}, 500


@app.get("/status")
def status():
    return telegram("getWebhookInfo")


@app.post("/telegram-webhook")
def telegram_webhook():

    update = request.get_json(silent=True) or {}

    print("UPDATE RECEIVED:", update, flush=True)

    # رسائل البوت العادي
    message = update.get("message")

    if message:

        chat_id = message.get("chat", {}).get("id")
        text = (message.get("text") or "").strip()

        if chat_id is None:
            return "ok", 200

        if text.startswith("/start"):

            reply = (
                "هلا 👋\n"
                "أنا بوت إدارة المحادثات 🤖\n"
                "وأقدر أساعد في الرد على الرسائل."
            )

        elif text.startswith("/help"):

            reply = (
                "الأوامر المتاحة:\n\n"
                "/start - تشغيل البوت\n"
                "/help - المساعدة\n"
                "/status - حالة البوت"
            )

        elif text.startswith("/status"):

            reply = "البوت شغال ✅"

        else:

            try:
                reply = get_ai_reply(text)

            except Exception as e:
                print("AI ERROR:", e, flush=True)
                reply = "صار خطأ بسيط، حاول مرة ثانية 😊"

        telegram(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": reply
            }
        )

        return "ok", 200


    # رسائل Telegram Business
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
            return "ok", 200

        if chat_id is None:
            return "ok", 200

        try:

            # إظهار "يكتب..." أثناء تجهيز الرد
            telegram(
                "sendChatAction",
                {
                    "business_connection_id": business_connection_id,
                    "chat_id": chat_id,
                    "action": "typing"
                }
            )

            reply = get_ai_reply(text)

            telegram(
                "sendMessage",
                {
                    "business_connection_id": business_connection_id,
                    "chat_id": chat_id,
                    "text": reply
                }
            )

            print(
                "REPLY SENT:",
                reply,
                flush=True
            )

        except Exception as e:

            print(
                "REPLY ERROR:",
                e,
                flush=True
            )

    return "ok", 200
