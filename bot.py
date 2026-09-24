import os
from flask import Flask, request
from telethon import TelegramClient, events
from google import genai
from google.genai import types

# =========================
# إعدادات الحساب
# =========================

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

MODEL = "gemini-2.5-flash"

app = Flask(__name__)

gemini = genai.Client(api_key=GEMINI_API_KEY)

client = TelegramClient(
    "telegram_user_session",
    API_ID,
    API_HASH
)

SYSTEM_PROMPT = """
أنت مساعد شخصي للرد على رسائل Telegram.

مهمتك الرد على الأشخاص الذين يرسلون رسائل إلى صاحب الحساب بطريقة طبيعية ودودة ومحترمة.

القواعد:
- اكتب بالعربية بشكل أساسي.
- استخدم اللهجة السعودية بشكل خفيف وطبيعي.
- اجعل الرد مختصرًا وواضحًا.
- افهم الرسالة ثم أجب مباشرة.
- لا تذكر أنك روبوت أو ذكاء اصطناعي إلا إذا سُئلت مباشرة.
- لا تخترع معلومات أو مواعيد أو أسعار.
- إذا لم تعرف الإجابة، قل إنك تحتاج للتأكد.
- لا تكشف كلمات المرور أو الرموز أو البيانات الخاصة.
- إذا احتاج الموضوع تدخل صاحب الحساب، قل إن صاحب الحساب سيرد لاحقًا.
- استخدم الإيموجي باعتدال 😊
"""


def get_ai_reply(text):
    response = gemini.models.generate_content(
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


@app.get("/")
def home():
    return "Telegram AI User Bot is running."


@app.get("/health")
def health():
    return "OK"


@client.on(events.NewMessage(incoming=True))
async def handle_message(event):

    # نتجاهل رسائل البوتات
    sender = await event.get_sender()

    if getattr(sender, "bot", False):
        return

    text = event.raw_text.strip()

    if not text:
        return

    print("NEW MESSAGE:", text, flush=True)

    try:
        reply = get_ai_reply(text)

        print("AI REPLY:", reply, flush=True)

        await event.reply(reply)

        print("REPLY SENT", flush=True)

    except Exception as e:
        print("REPLY ERROR:", e, flush=True)


def start_telegram():
    print("Starting Telegram client...", flush=True)

    client.start()

    print("Telegram client started.", flush=True)

    client.run_until_disconnected()


if __name__ == "__main__":
    start_telegram()
