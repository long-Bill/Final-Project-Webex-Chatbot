import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

WEBEX_BOT_TOKEN = os.getenv("WEBEX_BOT_TOKEN")

if not WEBEX_BOT_TOKEN:
    raise RuntimeError("WEBEX_BOT_TOKEN is not set")

WEBEX_API_URL = "https://webexapis.com/v1"

app = Flask(__name__)

def send_message(room_id: str, text: str):
    headers = {
        "Authorization": f"Bearer {WEBEX_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"roomId": room_id, "markdown": text}
    r = requests.post(f"{WEBEX_API_URL}/messages", json=payload, headers=headers)
    r.raise_for_status()

@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    # Webex sends notification wrapper; ignore if not a message
    if data.get("resource") != "messages" or data.get("event") != "created":
        return jsonify({"status": "ignored"}), 200

    message_id = data["data"]["id"]
    room_id = data["data"]["roomId"]
    person_email = data["data"]["personEmail"]

    # Avoid responding to our own messages
    if person_email.endswith("@webex.bot"):
        return jsonify({"status": "bot message ignored"}), 200

    # Fetch actual message text
    headers = {"Authorization": f"Bearer {WEBEX_BOT_TOKEN}"}
    msg_resp = requests.get(f"{WEBEX_API_URL}/messages/{message_id}", headers=headers)
    msg_resp.raise_for_status()
    text = msg_resp.json().get("text", "").strip().lower()

    # Simple command router
    if text.startswith("/fact"):
        reply = "Useless fact of the day: Honey never spoils."
    elif text.startswith("/weather"):
        reply = "Weather on demand: (you’d call a real API here)."
    elif text.startswith("/nasa"):
        reply = "NASA Picture of the Day: (call NASA API here)."
    else:
        reply = (
            "Hi! I understand:\n"
            "`/fact` – useless fact of the day\n"
            "`/weather` – weather on demand\n"
            "`/nasa` – NASA picture of the day"
        )

    send_message(room_id, reply)
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
