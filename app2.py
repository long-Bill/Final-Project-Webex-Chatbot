import os
import time
import requests
from flask import Flask, request, jsonify
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# --- Config ---
BOT_TOKEN = os.getenv("WEBEX_BOT_TOKEN", "NTAxOTA0MGQtNzlkNS00ZjU4LWIyZDktYTVhNzE2ZjBiZjJlN2M4ZGM3MDEtNzZm_P0A1_e58072af")
BOT_EMAIL = os.getenv("WEBEX_BOT_EMAIL", "myWeather-bot@webex.bot")
NASA_API_KEY = os.getenv("NASA_API_KEY", "HQNSZgpricGsiXaHrNRYfikWePsDTZmIEBSlRixf")
PORT = int(os.getenv("PORT", "5000"))

WAPI = "https://webexapis.com/v1"
WHEAD = {"Authorization": f"Bearer {BOT_TOKEN}", "Content-Type": "application/json"}

# --- Metrics ---
REQS = Counter("webexbot_requests_total", "HTTP requests", ["endpoint"])
ERRS = Counter("webexbot_errors_total", "Errors", ["type"])
LAT = Histogram("webexbot_handler_latency_seconds", "Webhook handler latency")
MSG_SENT = Counter("webexbot_messages_sent_total", "Messages sent")
CMD_USED = Counter("webexbot_command_used_total", "Commands used", ["cmd"])

# --- Helpers ---
def post_webex_markdown(room_id: str, text: str):
    r = requests.post(f"{WAPI}/messages", headers=WHEAD, json={"roomId": room_id, "markdown": text}, timeout=10)
    if r.ok:
        MSG_SENT.inc()
    return r

def get_message(mid: str):
    r = requests.get(f"{WAPI}/messages/{mid}", headers=WHEAD, timeout=10)
    r.raise_for_status()
    return r.json()

def is_from_bot(person_email: str) -> bool:
    return BOT_EMAIL and person_email.lower() == BOT_EMAIL.lower()

def cmd_weather(args):
    """ /weather <lat> <lon> (Open-Meteo) """
    try:
        lat = float(args[0]); lon = float(args[1])
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
               f"&current_weather=true")
        s = time.time()
        r = requests.get(url, timeout=10); r.raise_for_status()
        d = r.json().get("current_weather", {})
        LAT.observe(time.time() - s)
        CMD_USED.labels(cmd="weather").inc()
        if not d:
            return f"Could not fetch weather for `{lat},{lon}`."
        return (f"**Weather** for `{lat}, {lon}`\n"
                f"- Temp: **{d.get('temperature','?')}°C**\n"
                f"- Wind: **{d.get('windspeed','?')} m/s**\n"
                f"- Time: `{d.get('time','?')}`")
    except Exception as e:
        ERRS.labels(type="weather").inc()
        return f"Weather error: {e}"

def cmd_fact():
    """ random useless fact """
    try:
        r = requests.get("https://uselessfacts.jsph.pl/random.json?language=en", timeout=10)
        r.raise_for_status()
        CMD_USED.labels(cmd="fact").inc()
        return f"**Fact:** {r.json().get('text','(no fact)')}"
    except Exception as e:
        ERRS.labels(type="fact").inc()
        return f"Fact error: {e}"

def cmd_nasa():
    """ NASA Picture of the Day (title + url) """
    try:
        url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
        r = requests.get(url, timeout=10); r.raise_for_status()
        j = r.json()
        CMD_USED.labels(cmd="nasa").inc()
        return f"**NASA APOD:** {j.get('title','')}\n{j.get('url','')}"
    except Exception as e:
        ERRS.labels(type="nasa").inc()
        return f"NASA error: {e}"

def help_text():
    return (
        "**Commands**\n"
        "- `/weather <lat> <lon>` — Get current weather\n"
        "- `/fact` — Random useless fact\n"
        "- `/nasa` — NASA picture of the day\n"
        "- `/help` — This help\n"
    )

# --- Routes ---
@app.route("/metrics")
def metrics():
    REQS.labels(endpoint="/metrics").inc()
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

@app.route("/health")
def health():
    REQS.labels(endpoint="/health").inc()
    return jsonify({"ok": True}), 200

@app.route("/webex", methods=["POST"])
def webex():
    REQS.labels(endpoint="/webex").inc()
    start = time.time()
    data = request.get_json(force=True, silent=True) or {}
    try:
        # Only handle message created events
        if data.get("resource") != "messages" or data.get("event") != "created":
            return "", 204

        mid = data["data"]["id"]
        person_email = data["data"].get("personEmail", "")
        room_id = data["data"]["roomId"]

        # Ignore our own messages
        if is_from_bot(person_email):
            return "", 204

        # Fetch the message text
        msg = get_message(mid).get("text", "").strip()
        # Parse commands
        if msg.startswith("/weather"):
            parts = msg.split()
            if len(parts) != 3:
                post_webex_markdown(room_id, "Usage: `/weather <lat> <lon>`")
            else:
                post_webex_markdown(room_id, cmd_weather(parts[1:]))
        elif msg.startswith("/fact"):
            post_webex_markdown(room_id, cmd_fact())
        elif msg.startswith("/nasa"):
            post_webex_markdown(room_id, cmd_nasa())
        elif msg.startswith("/help"):
            post_webex_markdown(room_id, help_text())
        else:
            # Friendly default
            post_webex_markdown(room_id, "Hi! Type `/help` for commands.")
        return "", 200
    except Exception as e:
        ERRS.labels(type="webhook").inc()
        post_webex_markdown(room_id, f"Error: {e}")
        return "", 200
    finally:
        LAT.observe(time.time() - start)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
