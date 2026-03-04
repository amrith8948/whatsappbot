from fastapi import FastAPI, Request
import requests
import os
from datetime import datetime

app = FastAPI()

# ===============================
# ENV VARIABLES
# ===============================

WATI_TOKEN = os.getenv("WATI_TOKEN")
WATI_BASE_URL = os.getenv("WATI_BASE_URL")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

TABLE_NAME = "admissions_chat"

# ===============================
# BROCHURE LOCKED DATA
# ===============================

BROCHURE_KNOWLEDGE = """
ACCA:
- Coaching Fee: ₹3,50,000 – ₹4,50,000
- Duration: 2–3 years
- Structured mentoring included.

CMA:
- Coaching Fee: ₹2,50,000 – ₹3,50,000
- Duration: 1.5–2 years

Scholarship:
- Installment support available.
"""

# ===============================
# AI RESPONSE
# ===============================

def generate_ai_response(user_input):

    system_prompt = f"""
You are an academic counsellor at Invisor Global.

Use ONLY this data:

{BROCHURE_KNOWLEDGE}

Rules:
- Do NOT add outside info.
- Keep response under 120 words.
- Friendly tone.
"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        "temperature": 0.4
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=data
    )

    return response.json()["choices"][0]["message"]["content"]

# ===============================
# SAVE TO SUPABASE
# ===============================

def save_to_supabase(phone, message):

    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "phone_number": phone,
        "full_chat": [{"role": "user", "content": message}],
        "created_at": datetime.utcnow().isoformat()
    }

    requests.post(url, headers=headers, json=data)

# ===============================
# SEND MESSAGE BACK TO WATI
# ===============================

def send_wati_message(phone, message):

    url = f"{WATI_BASE_URL}/api/v1/sendSessionMessage/{phone}"

    headers = {
        "Authorization": f"Bearer {WATI_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messageText": message
    }

    requests.post(url, headers=headers, json=data)

# ===============================
# WEBHOOK ENDPOINT
# ===============================

@app.post("/webhook")
async def webhook(request: Request):

    body = await request.json()

    phone = body["waId"]
    message = body["text"]

    reply = generate_ai_response(message)

    save_to_supabase(phone, message)

    send_wati_message(phone, reply)

    return {"status": "success"}
