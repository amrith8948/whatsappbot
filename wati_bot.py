from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

# WATI credentials from Render Environment Variables
WATI_API_KEY = os.getenv("WATI_API_KEY")
WATI_BASE_URL = os.getenv("WATI_BASE_URL")

# Root route (prevents "Not Found" error)
@app.get("/")
def home():
    return {"message": "WhatsApp Bot is running 🚀"}

# Webhook endpoint (WATI will send messages here)
@app.post("/webhook")
async def webhook(request: Request):
    
    data = await request.json()
    print("Incoming data:", data)

    try:
        message = data["text"]
        phone = data["from"]

        reply = generate_reply(message)

        send_message(phone, reply)

        return {"status": "success"}

    except Exception as e:
        print("Error:", e)
        return {"status": "error", "message": str(e)}


# Bot reply logic
def generate_reply(message):

    message = message.lower()

    if "hello" in message:
        return "Hi 👋 How can I help you today?"

    elif "price" in message:
        return "Please visit our website for pricing details."

    elif "help" in message:
        return "Our support team will contact you shortly."

    else:
        return "Sorry, I didn't understand that. Please type *help*."


# Send message through WATI API
def send_message(phone, message):

    url = f"{WATI_BASE_URL}/api/v1/sendSessionMessage/{phone}"

    headers = {
        "Authorization": f"Bearer {WATI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "messageText": message
    }

    response = requests.post(url, json=payload, headers=headers)

    print("WATI response:", response.text)
