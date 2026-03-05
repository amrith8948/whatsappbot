from fastapi import FastAPI, Request
import requests
import os
from datetime import datetime

app = FastAPI()

# ==============================
# ENV VARIABLES
# ==============================

WATI_API_KEY = os.getenv("WATI_API_KEY")
WATI_BASE_URL = os.getenv("WATI_BASE_URL")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

TABLE_NAME = "admissions_chat"

# ==============================
# BROCHURE LOCKED DATA
# ==============================

BROCHURE_KNOWLEDGE = """
INVISOR GLOBAL OFFICIAL COURSE DETAILS:

ACCA:
- Coaching Fee: ₹3,50,000 – ₹4,50,000
- Duration: 2–3 years

CMA:
- Coaching Fee: ₹2,50,000 – ₹3,50,000
- Duration: 1.5–2 years

Scholarship:
- Installment guidance available.
"""

# ==============================
# LEAD TYPE
# ==============================

def calculate_lead_type(score):
    if score >= 80:
        return "Hot"
    elif score >= 40:
        return "Warm"
    return "Cold"

# ==============================
# FETCH EXISTING CHAT
# ==============================

def get_existing_lead(phone):

    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?phone_number=eq.{phone}"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200 and response.json():
        return response.json()[0]

    return None

# ==============================
# SAVE / UPDATE SUPABASE
# ==============================

def save_chat(phone, user_message, bot_reply):

    existing = get_existing_lead(phone)

    if existing:
        chat_history = existing["full_chat"]
        lead_tags = existing["lead_tags"]
        lead_score = existing["lead_score"]
        scholarship_interest = existing["scholarship_interest"]
    else:
        chat_history = []
        lead_tags = []
        lead_score = 0
        scholarship_interest = False

    chat_history.append({"role": "user", "content": user_message})
    chat_history.append({"role": "assistant", "content": bot_reply})

    lower = user_message.lower()

    if "acca" in lower and "ACCA interest" not in lead_tags:
        lead_tags.append("ACCA interest")
        lead_score += 40

    if "cma" in lower and "CMA interest" not in lead_tags:
        lead_tags.append("CMA interest")
        lead_score += 40

    if any(word in lower for word in ["budget", "can't afford", "financial"]):
        scholarship_interest = True
        lead_score += 30

    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?on_conflict=phone_number"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    data = {
        "phone_number": phone,
        "full_chat": chat_history,
        "lead_tags": lead_tags,
        "lead_score": lead_score,
        "lead_type": calculate_lead_type(lead_score),
        "scholarship_interest": scholarship_interest,
        "last_message": user_message,
        "updated_at": datetime.utcnow().isoformat()
    }

    requests.post(url, headers=headers, json=data)

# ==============================
# AI RESPONSE
# ==============================

def generate_ai_reply(user_message):

    system_prompt = f"""
You are an academic counsellor.

Use ONLY this data:
{BROCHURE_KNOWLEDGE}

Rules:
- Don't invent numbers
- Keep friendly tone
- Under 100 words
"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.4
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload
    )

    if response.status_code != 200:
        return "Our academic counsellor will guide you personally."

    return response.json()["choices"][0]["message"]["content"]

# ==============================
# SEND MESSAGE VIA WATI
# ==============================

def send_message(phone, message):

    url = f"{WATI_BASE_URL}/api/v1/sendSessionMessage/{phone}"

    headers = {
        "Authorization": f"Bearer {WATI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {"messageText": message}

    requests.post(url, json=payload, headers=headers)

# ==============================
# WEBHOOK
# ==============================

@app.post("/webhook")
async def webhook(request: Request):

    data = await request.json()

    try:
        user_message = data["text"]
        phone = data["from"]

        bot_reply = generate_ai_reply(user_message)

        save_chat(phone, user_message, bot_reply)

        send_message(phone, bot_reply)

        return {"status": "success"}

    except Exception as e:
        return {"status": "error", "message": str(e)}
