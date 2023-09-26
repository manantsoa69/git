import os
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
import requests

from gpt_chat import chat_with_gpt

# Load environment variables from the .env file
load_dotenv()

app = FastAPI()

# You can access the environment variables like this
PAGE_ACCESS_TOKEN = os.getenv("TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

@app.get("/")
async def home():
    print("Home endpoint reached")
    return {"message": "OK"}

@app.get("/webhook")
async def verify_webhook(hub_challenge: str, hub_verify_token: str):
    if hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    else:
        raise HTTPException(status_code=403, detail="Invalid verification token")

@app.post("/webhook")
async def receive_webhook(data: dict):
    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                sender_id = messaging_event["sender"]["id"]
                recipient_id = messaging_event["recipient"]["id"]
                if "message" in messaging_event:
                    message_text = messaging_event["message"]["text"]
                    print(f"User's question: {message_text}")
                    await handle_message(sender_id, message_text)
    return "OK"

async def send_message(sender_id, message_text):
    message_data = {"recipient": {"id": sender_id}, "message": {"text": message_text}}

    response = requests.post(
        f"https://graph.facebook.com/v13.0/me/messages?access_token={PAGE_ACCESS_TOKEN}",
        json=message_data,
    )

    if response.status_code == 200:
        print("Message sent successfully")
    else:
        print("Failed to send message")

async def handle_message(sender_id, message_text):
    response_text = await chat_with_gpt(message_text)
    await send_message(sender_id, response_text)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
