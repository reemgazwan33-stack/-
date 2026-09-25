import os
import requests
from flask import Flask, request
from google import genai
from google.genai import types

BOT_TOKEN = os.environ["BOT_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

MODEL = "gemini-2.5-flash"
WEBHOOK_URL = "https://telegram-ai-bot-335e.onrender.com/telegram-webhook"

app = Flask(__name__)
client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
أنت مساعد شخصي للرد على رسائل Telegram.

مهمتك الرد على الأشخاص الذين يرسلون رسائل إلى الحساب بطريقة طبيعية وودودة.

القواعد:
- اكتب بالعربية بشكل أساسي.
- استخدم اللهجة السعودية بشكل خفيف وطبيعي.
- افهم الرسالة ثم أجب مباشرة.
- اجعل الرد مختصرًا وواضحًا.
- لا تذكر أنك روبوت أو ذكاء اصطناعي إلا إذا سُئلت مباشرة.
- لا تخترع معلومات أو أسعار أو مواعيد.
- إذا لم تعرف الإجابة، قل إنك تحتاج للتأكد.
- استخدم الإيموجي باعتدال 😊
- إذا كانت الرسالة تحية، رد بتحية لطيفة.
- إذا كانت الرسالة غير واضحة، اطلب توضيحًا بسيطًا.
- إذا احتاج الموضوع صاحب الحساب، أخبر الشخص أن صاحب الحساب سيرد عليه لاحقًا.
"""

def telegram(method, data=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    response = requests.post(url, json=data or {}, timeout=60)
    return response.json()

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

    reply
