import os
import requests
from flask import Flask, request
from google import genai
from google.genai import types

BOT_TOKEN = os.environ["BOT_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

MODEL = "gemini-2.5-flash"

app = Flask(__name__)

client = genai.Client(api_key=GEMINI_API_KEY)

WEBHOOK_URL = "https://telegram-ai-bot-335e.onrender.com/telegram-webhook"

SYSTEM_PROMPT = """
أنت مساعد شخصي للرد على رسائل Telegram.

مهمتك الرد على الأشخاص الذين يرسلون رسائل إلى الحساب بطريقة طبيعية، ودودة، ومحترمة.

قواعد الرد:
- اكتب بالعربية بشكل أساسي، واستخدم اللهجة السعودية بشكل خفيف وطبيعي.
- اجعل الرد مختصرًا وواضحًا.
- افهم سؤال الشخص ثم أجب مباشرة.
- لا تذكر أنك روبوت أو ذكاء اصطناعي إلا إذا سُئلت بشكل مباشر.
- لا تخترع معلومات أو مواعيد أو أسعار أو وعود غير معروفة.
- إذا لم تعرف الإجابة، قل إنك تحتاج للتأكد.
- لا ترسل رسائل كثيرة متتالية.
- كن لطيفًا وطبيعيًا.
- استخدم الإيموجي باعتدال 😊
- إذا كانت الرسالة تحية، رد بتحية لطيفة.
- إذا كانت الرسالة غير واضحة، اطلب توضيحًا بسيطًا.
- لا تكشف أي معلومات خاصة أو كلمات مرور أو رموز أو بيانات حساسة.
- إذا احتاج الموضوع تدخل صاحب الحساب، قل إن صاحب الحساب سيرد عليه لاحقًا.
"""


@app.get("/")
def home():
    return "Telegram AI Bot is running."


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
        return "أحتاج أتأكد من الموضوع وأرجع لك."

    return reply


@app.post("/telegram-webhook")
def telegram_webhook():

    update = request.get_json(silent=True) or {}

    print("UPDATE RECEIVED:", update, flush=True)

    message = update.get("business_message")

    if not message:
        return "ok", 200

    text = message.get("text")
    business_connection_id = message.get("business_connection_id")
    chat_id = message.get("chat", {}).get("id")

    if not text:
        return "ok", 200

    if not business_connection_id:
        print("No business_connection_id", flush=True)
        return "ok", 200

    if chat_id is None:
        print("No chat_id", flush=True)
        return "ok", 200

    print("NEW MESSAGE:", text, flush=True)

    try:
        reply = get_ai_reply(text)

        print("AI REPLY:", reply, flush=True)

        telegram(
            "sendMessage",
            {
                "business_connection_id": business_connection_id,
                "chat_id": chat_id,
                "text": reply
            }
        )

        print("REPLY SENT", flush=True)

    except Exception as e:
        print("REPLY ERROR:", e, flush=True)

    return "ok", 200


# تسجيل Webhook في Telegram
try:
    result = telegram(
        "setWebhook",
        {
            "url": WEBHOOK_URL,
            "allowed_updates": ["business_message"],
            "drop_pending_updates": False
        }
    )

    print("WEBHOOK SET:", result, flush=True)

except Exception as e:
    print("WEBHOOK ERROR:", e, flush=True)
    
@app.get("/setup")
def setup():
    try:
        result = telegram(
            "setWebhook",
            {
                "url": WEBHOOK_URL,
                "allowed_updates": ["business_message"],
                "drop_pending_updates": False
            }
        )
        return result
    except Exception as e:
        return {"error": str(e)}, 500
