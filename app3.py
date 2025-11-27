import os
import time
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

WEBEX_BOT_TOKEN = os.getenv("WEBEX_BOT_TOKEN")
if not WEBEX_BOT_TOKEN:
    raise RuntimeError("WEBEX_BOT_TOKEN is not set")

WEBEX_API_URL = "https://webexapis.com/v1"
NASA_API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")

app = Flask(__name__)


def send_message(room_id: str, text: str):
    headers = {
        "Authorization": f"Bearer {WEBEX_BOT_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"roomId": room_id, "markdown": text}
    r = requests.post(
        f"{WEBEX_API_URL}/messages",
        json=payload,
        headers=headers,
        timeout=10,
    )
    r.raise_for_status()


# -------------------------
# NASA APOD API CALL
# -------------------------
def fetch_nasa_apod():
    url = "https://api.nasa.gov/planetary/apod"
    params = {"api_key": NASA_API_KEY}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


# -------------------------
# USELESS FACTS API CALL
# -------------------------
def fetch_useless_fact():
    url = "https://uselessfacts.jsph.pl/api/v2/facts/random"
    headers = {"Accept": "application/json"}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()
    return data.get("text", "I couldn't get a useless fact.")


# -------------------------------------------
# WEATHER.GOV API CALL
# -------------------------------------------
def fetch_weather_forecast():
    # Step 1: Get metadata from points API
    points_url = (
        "https://api.weather.gov/points/"
        "34.061417224159996,-117.81999390574555"
    )
    headers = {"User-Agent": "SDN-Project-Bot/1.0"}  # REQUIRED by weather.gov

    r1 = requests.get(points_url, headers=headers, timeout=10)
    r1.raise_for_status()
    points_data = r1.json()

    forecast_url = points_data["properties"]["forecast"]

    # Step 2: Request forecast
    r2 = requests.get(forecast_url, headers=headers, timeout=10)
    r2.raise_for_status()
    forecast_data = r2.json()

    periods = forecast_data["properties"]["periods"]
    next_period = periods[0]  # first forecast period

    name = next_period["name"]
    temp = next_period["temperature"]
    unit = next_period["temperatureUnit"]
    forecast = next_period["detailedForecast"]

    return f"**{name}**\nTemperature: **{temp}°{unit}**\n{forecast}"


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
    msg_resp = requests.get(
        f"{WEBEX_API_URL}/messages/{message_id}",
        headers=headers,
        timeout=10,
    )
    msg_resp.raise_for_status()
    text = msg_resp.json().get("text", "").strip().lower()

    # Simple command router
    if text.startswith("/fact"):
        try:
            fact = fetch_useless_fact()
            reply = f"**Useless fact of the day:**\n\n{fact}"
        except Exception:
            reply = (
                "I tried to fetch a useless fact, but something went wrong 😕\n"
                "Please try again later."
            )

    elif text.startswith("/weather"):
        try:
            weather = fetch_weather_forecast()
            reply = f"**Weather Forecast:**\n\n{weather}"
        except Exception:
            reply = (
                "I tried to fetch the weather, but something went wrong 😕\n"
                "Please try again later."
            )

    elif text.startswith("/nasa"):
        try:
            apod = fetch_nasa_apod()

            # Optionally truncate the explanation for chat friendliness
            explanation = apod.get("explanation", "")
            max_len = 600
            if len(explanation) > max_len:
                explanation = explanation[:max_len].rsplit(" ", 1)[0] + "..."

            # Build a nice Markdown message for Webex
            reply = (
                f"**NASA Astronomy Picture of the Day**\n\n"
                f"**{apod.get('title', 'No title')}** "
                f"({apod.get('date', '')})\n\n"
                f"{explanation}\n\n"
            )

            if apod.get("url"):
                reply += f"[View image or media]({apod['url']})"

        except requests.HTTPError as e:
            reply = (
                "I tried to reach the NASA APOD API, but got an HTTP error.\n"
                f"`{e}`"
            )
        except Exception:
            reply = (
                "Something went wrong while fetching the NASA Picture of the Day. 😕\n"
                "Please try again later."
            )

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
