import os
import time
import json
import threading
import requests
from flask import Flask
from google import genai
from google.genai import types

# =========================
# الإعدادات
# =========================

BOT_TOKEN = os.environ["BOT_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

MODEL = "gemini-2.5-flash"

client = genai.Client(api_key=GEMINI_API_KEY)

app = Flask(__name__)

SYSTEM_PROMPT = """
أنت مساعد شخصي للرد على رسائل Telegram.

مهمتك الرد على الأشخاص الذين يرسلون رسائل إلى الحساب بطريقة طبيعية، ودودة، ومحترمة.

قواعد الرد:
- اكتب بالعربية بشكل أساسي.
- استخدم اللهجة السعودية بشكل خفيف وطبيعي.
- اجعل الرد مختصرًا وواضحًا.
- افهم سؤال الشخص ثم أجب مباشرة.
- لا تقل إنك روبوت أو ذكاء اصطناعي إلا إذا سُئلت مباشرة.
- لا تخترع معلومات أو أسعارًا أو مواعيد أو وعودًا.
- إذا لم تعرف الإجابة، قل إنك تحتاج للتأكد.
- لا ترسل عدة رسائل متتالية.
- استخدم الإيموجي باعتدال 😊
- إذا كانت الرسالة تحية، رد بتحية لطيفة.
- إذا كانت الرسالة غير واضحة، اطلب توضيحًا بسيطًا.
- لا تكشف أي معلومات خاصة أو كلمات مرور أو رموز.
- لا تتخذ قرارات مهمة نيابة عن صاحب الحساب.
"""

# =========================
# صفحة Render
# =========================

@app.get("/")
def home():
    return "Telegram AI Bot is running."


# =========================
# Telegram API
# =========================

def telegram(method, data=None, timeout=60):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"

    response = requests.post(
        url,
        json=data or {},
        timeout=timeout
    )

    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):
        raise Exception(result)

    return result


# =========================
# الذكاء الاصطناعي
# =========================

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


# =========================
# استقبال رسائل Telegram
# =========================

def run_bot():

    print("BOT STARTING...", flush=True)

    # حذف أي Webhook قديم حتى يعمل getUpdates
    try:
        telegram(
            "deleteWebhook",
            {
                "drop_pending_updates": False
            }
        )

        print("Webhook deleted.", flush=True)

    except Exception as e:
        print("Webhook error:", e, flush=True)

    offset = None

    print("POLLING STARTED.", flush=True)

    while True:

        try:

            params = {
                "timeout": 50
            }

            if offset is not None:
                params["offset"] = offset

            response = requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
                params=params,
                timeout=60
            )

            data = response.json()

            if not data.get("ok"):
                print("Telegram error:", data, flush=True)
                time.sleep(5)
                continue

            updates = data.get("result", [])

            for update in updates:

                offset = update["update_id"] + 1

                print(
                    "UPDATE:",
                    json.dumps(update, ensure_ascii=False),
                    flush=True
                )

                # رسالة Telegram Business
                message = update.get("business_message")

                if not message:
                    continue

                text = message.get("text")

                business_connection_id = message.get(
                    "business_connection_id"
                )

                chat_id = message.get(
                    "chat",
                    {}
                ).get("id")

                if not text:
                    print("No text message.", flush=True)
                    continue

                if not business_connection_id:
                    print(
                        "No business_connection_id.",
                        flush=True
                    )
                    continue

                if chat_id is None:
                    print(
                        "No chat_id.",
                        flush=True
                    )
                    continue

                print(
                    f"NEW MESSAGE: {text}",
                    flush=True
                )

                try:

                    reply = get_ai_reply(text)

                    print(
                        f"AI REPLY: {reply}",
                        flush=True
                    )

                    telegram(
                        "sendMessage",
                        {
                            "business_connection_id":
                                business_connection_id,

                            "chat_id":
                                chat_id,

                            "text":
                                reply
                        }
                    )

                    print(
                        "REPLY SENT.",
                        flush=True
                    )

                except Exception as e:

                    print(
                        "REPLY ERROR:",
                        e,
                        flush=True
                    )

        except Exception as e:

            print(
                "POLL ERROR:",
                e,
                flush=True
            )

            time.sleep(5)


# =========================
# تشغيل البوت
# =========================

threading.Thread(
    target=run_bot,
    daemon=True
).start()
