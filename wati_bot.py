from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

WHATSAPP_TOKEN = "EAAc668Q1pmcBQZC1jiHd20q5uYuvg3Wp1hoJuUc7U4ODwFjmTtQhVbneEKMul7a4fgf32bUHyEXPkkbz289S6ScYTcZBBmcScBOZCEGTWx70SM38FuM65iahNiMjadDBMtNovYhZClfKpZAiegILWZBvggzz39V95D1DlUoHIMYKbGN05HYN2HaTQTRvhvqhPxnyyPXIXBlXb2IiNbfmvuQsIszoP9sZADCtntZAQKgBbaCTUXry98iPQveqFWUuPAzvxoDWBV0i2R8NbYuF0G4oFdXU"
PHONE_NUMBER_ID = "935539746319902"
VERIFY_TOKEN = "myverify123"

# ✅ Webhook Verification (Meta Requirement)
@app.get("/webhook")
async def verify(request: Request):
    params = request.query_params
    if params.get("hub.verify_token") == VERIFY_TOKEN:
        return int(params.get("hub.challenge"))
    return "Verification failed"

# ✅ Receive Incoming Messages
@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        phone = message["from"]
        text = message["text"]["body"]

        print("Received:", text)

        reply = f"AI Reply: You said '{text}'"

        send_message(phone, reply)

    except:
        pass

    return {"status": "ok"}


def send_message(phone, message):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": message}
    }

    requests.post(url, headers=headers, json=payload)
