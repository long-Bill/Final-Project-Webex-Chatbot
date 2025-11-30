######################################################################################
# This program:
# - Loads config (token, optional room id) from a .env file.
# - If WEBEX_ROOM_ID is not set, lists the user's Webex rooms and asks which to monitor.
# - Monitors the selected Webex room every second for "/astros" messages.
# - Uses the Open Notify "People In Space" API to find out who is in space.
# - Formats and sends the results back to the Webex room.
######################################################################################

import os
import time
import json
import requests
from dotenv import load_dotenv

#######################################################################################
# Webex API Base URL
# - Commercial Webex: https://webexapis.com/v1
# - Webex for Government: https://api-usgov.webex.com/v1
#######################################################################################

WEBEX_API_BASE = "https://webexapis.com/v1"


#######################################################################################
# 0. Load environment variables from .env
#######################################################################################

# This will read a .env file in the same directory as people_in_space_chatbot.py (if present)
load_dotenv()

#######################################################################################
# 1. Ask user for their Personal Access Token (instead of reading from .env)
#######################################################################################

personal_access_token = input("Please enter your Webex Personal Access Token: ").strip()

if not personal_access_token:
    raise RuntimeError(
        "No Personal Access Token entered. A token is required to continue."
    )


accessToken = "Bearer " + personal_access_token

# Optional: room to use directly (skips interactive selection if present)
CONFIGURED_ROOM_ID = os.getenv("WEBEX_ROOM_ID")

#######################################################################################
# 2. If no room id in env, list rooms and let user choose
#######################################################################################

roomIdToGetMessages = None
roomTitleToGetMessages = None

if CONFIGURED_ROOM_ID:
    roomIdToGetMessages = CONFIGURED_ROOM_ID
    print(f"Using room id from WEBEX_ROOM_ID: {roomIdToGetMessages}")

    # (Optional) try to look up the room name for nicer logs
    r = requests.get(
        f"{WEBEX_API_BASE}/rooms",
        headers={"Authorization": accessToken}
    )
    if r.status_code == 200:
        rooms = r.json().get("items", [])
        for room in rooms:
            if room.get("id") == roomIdToGetMessages:
                roomTitleToGetMessages = room.get("title")
                break
    if roomTitleToGetMessages:
        print(f"Room title: {roomTitleToGetMessages}")
    else:
        print("Could not resolve room title (but id is configured).")

else:
    # No WEBEX_ROOM_ID configured: list rooms and prompt the user

    r = requests.get(
        f"{WEBEX_API_BASE}/rooms",
        headers={"Authorization": accessToken}
    )

    if not r.status_code == 200:
        raise Exception(
            "Incorrect reply from Webex API. Status code: {}. Text: {}".format(
                r.status_code, r.text
            )
        )

    print("\nList of available rooms:")
    rooms = r.json()["items"]
    for room in rooms:
        print("Type: '{}' Name: {}".format(room["type"], room["title"]))

    # SEARCH FOR WEBEX ROOM TO MONITOR
    while True:
        roomNameToSearch = input(
            "Which room should be monitored for the /astros messages? "
        )
        for room in rooms:
            if room["title"].find(roomNameToSearch) != -1:
                print("Found rooms with the word " + roomNameToSearch)
                print(room["title"])
                roomIdToGetMessages = room["id"]
                roomTitleToGetMessages = room["title"]
                print("Found room: " + roomTitleToGetMessages)
                break

        if roomIdToGetMessages is None:
            print("Sorry, I didn't find any room with " + roomNameToSearch + " in it.")
            print("Please try again...")
        else:
            break

if not roomIdToGetMessages:
    raise RuntimeError("No room id selected or configured; cannot continue.")

######################################################################################
# 3. Webex bot loop: listen for /astros and respond with people in space
######################################################################################

print("Monitoring room for /astros messages...")

while True:
    # Poll every second
    time.sleep(1)

    GetParameters = {
        "roomId": roomIdToGetMessages,
        "max": 1
    }

    r = requests.get(
        f"{WEBEX_API_BASE}/messages",
        params=GetParameters,
        headers={"Authorization": accessToken}
    )

    if not r.status_code == 200:
        raise Exception(
            "Incorrect reply from Webex API. Status code: {}. Text: {}".format(
                r.status_code, r.text
            )
        )

    json_data = r.json()
    if len(json_data["items"]) == 0:
        print("There are no messages in the room yet.")
        continue

    messages = json_data["items"]
    message = messages[0]["text"].strip()
    print("Received message: " + message)

    # Only respond to /astros
    if not message.lower().startswith("/astros"):
        continue

    ############################################################################
    # Call the Open Notify "People In Space" API
    ############################################################################

    people_api_url = "http://api.open-notify.org/astros.json"

    try:
        r = requests.get(people_api_url, timeout=10)

        # Non-200 response
        if r.status_code != 200:
            raise Exception(
                f"Open Notify API returned status {r.status_code}: {r.text}"
            )

        astros_data = r.json()

        if astros_data.get("message") != "success":
            raise Exception("Open Notify API returned a non-success message.")

        number_in_space = astros_data.get("number", 0)
        people = astros_data.get("people", [])

        if number_in_space == 0 or not people:
            responseMessage = (
                "According to Open Notify, there are currently no humans in space. 🌍"
            )
        else:
            lines = [
                f"- {person.get('name', 'Unknown')} ({person.get('craft', 'Unknown craft')})"
                for person in people
            ]
            people_list = "\n".join(lines)
            responseMessage = (
                f"There are currently {number_in_space} human(s) in space:\n{people_list}"
            )

    except Exception as e:
        # Log the error to the console
        print(f"[ERROR] Could not call Open Notify API: {e}")

        # Create a user-friendly Webex message
        responseMessage = (
            "⚠️ Sorry! I couldn't retrieve astronaut data right now. "
            "The Open Notify API appears to be unavailable. Please try again later."
        )

