######################################################################################
# Random Fact Webex Chatbot
#
# This program:
# - Loads config (WEBEX_ROOM_ID, etc.) from a .env file.
# - ALWAYS asks the user for their Webex Personal Access Token at runtime.
# - Monitors the configured Webex room for "/fact" commands.
# - Calls the uselessfacts API at https://uselessfacts.jsph.pl/api/v2/facts/random
#   to get a random fact.
# - Sends the fact back to the Webex room as a markdown message.
#
# .env example (same folder as this script):
#   WEBEX_ROOM_ID=Y2lzY29zcGFyazovL3VybjpURUFNOnVzLXdlc3QtMl9yL1JPT00v...
#   WEBEX_BOT_TOKEN=optional-bot-token-if-you-have-one
#   WEBEX_BOT_EMAIL=myWeather-bot@webex.bot
######################################################################################

import os
import time
import json
import requests
from dotenv import load_dotenv

######################################################################################
# Constants
######################################################################################

WEBEX_API_BASE = "https://webexapis.com/v1"
FACT_API_URL = "https://uselessfacts.jsph.pl/api/v2/facts/random"

######################################################################################
# Load environment variables
######################################################################################

load_dotenv()

WEBEX_ROOM_ID = os.getenv("WEBEX_ROOM_ID")
WEBEX_BOT_TOKEN = os.getenv("WEBEX_BOT_TOKEN")  # not used right now, but available

if not WEBEX_ROOM_ID:
    raise RuntimeError(
        "WEBEX_ROOM_ID is missing from .env. Please add it and try again."
    )

print(f"Loaded room ID from .env: {WEBEX_ROOM_ID}")

######################################################################################
# Ask user for Personal Access Token (ALWAYS)
######################################################################################

personal_access_token = input(
    "Enter your Webex Personal Access Token (NOT the bot token): "
).strip()

if not personal_access_token:
    raise RuntimeError("A Webex Personal Access Token is required to continue.")

accessToken = "Bearer " + personal_access_token

######################################################################################
# Optional: Look up the room title for nicer logging
######################################################################################

room_title = "(Unknown Title)"

try:
    rooms_resp = requests.get(
        f"{WEBEX_API_BASE}/rooms",
        headers={"Authorization": accessToken},
        timeout=10,
    )

    if rooms_resp.status_code == 200:
        items = rooms_resp.json().get("items", [])
        for room in items:
            if room.get("id") == WEBEX_ROOM_ID:
                room_title = room.get("title", room_title)
                break
    else:
        print(
            f"[WARN] Could not look up rooms. "
            f"Status {rooms_resp.status_code}: {rooms_resp.text}"
        )
except Exception as e:
    print(f"[WARN] Exception while looking up rooms: {e}")

print("\n--------------------------------------------------")
print(f"Monitoring Webex room:\n - ID: {WEBEX_ROOM_ID}\n - Title: {room_title}")
print("Waiting for /fact commands...\n")

######################################################################################
# Polling loop
######################################################################################

last_message_id = None  # track last processed message to avoid reprocessing

while True:
    time.sleep(1)

    params = {
        "roomId": WEBEX_ROOM_ID,
        "max": 1,  # only need the latest message
    }

    # Get latest message from the room
    try:
        msg_resp = requests.get(
            f"{WEBEX_API_BASE}/messages",
            params=params,
            headers={"Authorization": accessToken},
            timeout=10,
        )
    except Exception as e:
        print(f"[ERROR] Failed to contact Webex API for messages: {e}")
        continue

    if msg_resp.status_code != 200:
        print(
            f"[ERROR] Webex /messages returned {msg_resp.status_code}: "
            f"{msg_resp.text}"
        )
        continue

    items = msg_resp.json().get("items", [])
    if not items:
        # No messages in the room yet
        continue

    latest = items[0]
    message_id = latest.get("id")
    message_text = latest.get("text", "").strip()

    # Avoid processing the same message over and over
    if message_id == last_message_id:
        continue
    last_message_id = message_id

    print(f"Received: {message_text}")

    # Only act on /fact commands
    if not message_text.lower().startswith("/fact"):
        continue

    ###############################################################################
    # Call the uselessfacts API
    ###############################################################################

    try:
        fact_resp = requests.get(FACT_API_URL, timeout=10)

        if fact_resp.status_code != 200:
            raise Exception(
                f"Fact API returned {fact_resp.status_code}: {fact_resp.text}"
            )

        fact_json = fact_resp.json()

        # For https://uselessfacts.jsph.pl/api/v2/facts/random
        fact_text = fact_json.get("text", "No fact text found.")
        source = fact_json.get("source", "unknown")
        source_url = fact_json.get("source_url", "")

        if source_url:
            reply_markdown = (
                f"🧠 **Random Useless Fact**\n\n"
                f"{fact_text}\n\n"
                f"_Source: [{source}]({source_url})_"
            )
        else:
            reply_markdown = f"🧠 **Random Useless Fact**\n\n{fact_text}"

    except Exception as e:
        print(f"[ERROR] Fact API error: {e}")
        reply_markdown = (
            "⚠️ Sorry! I couldn't retrieve a fact right now. "
            "Please try again later."
        )

    ###############################################################################
    # Send the reply back to the Webex room
    ###############################################################################

    post_payload = {
        "roomId": WEBEX_ROOM_ID,
        "markdown": reply_markdown,
    }

    try:
        send_resp = requests.post(
            f"{WEBEX_API_BASE}/messages",
            headers={
                "Authorization": accessToken,
                "Content-Type": "application/json",
            },
            data=json.dumps(post_payload),
            timeout=10,
        )
    except Exception as e:
        print(f"[ERROR] Failed to send message to Webex: {e}")
        continue

    if send_resp.status_code != 200:
        print(
            f"[ERROR] Failed to send message. "
            f"Status {send_resp.status_code}: {send_resp.text}"
        )
    else:
        print("✔️ Fact sent!\n")
