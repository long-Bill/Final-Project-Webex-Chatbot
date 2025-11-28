######################################################################################
# This program:
# - Uses a hard coded access token.
# - Lists the user's Webex rooms.
# - Asks the user which Webex room to monitor for "/seconds" of requests.
# - Monitors the selected Webex Team room every second for "/seconds" messages.
# - Discovers GPS coordinates of the ISS flyover using ISS API.
# - Display the geographical location using Graphhopper API based on the GPS coordinates.
# - Formats and sends the results back to the Webex Team room.
######################################################################################

#######################################################################################
# 1. Import libraries for API requests, JSON formatting, parsing URLs into components,
#    and epoch time conversion.

import time
import requests
import json
import urllib
from urllib.parse import urlencode

#######################################################################################
# CONFIG: choose the correct Webex base URL:
# - For normal (commercial) Webex: https://webexapis.com/v1
# - For Webex for Government:     https://api-usgov.webex.com/v1
#######################################################################################
WEBEX_API_BASE = "https://webexapis.com/v1"  # change to api-usgov if needed

#######################################################################################
# 2. Hard-coded token is created and Bearer is added to meet auth token format
#######################################################################################

personal_access_token = None

# Hard-coded token (REPLACE token after "Bearer " to use a different token)
accessToken = "Bearer " + personal_access_token

#######################################################################################
# 3. Provide the URL to the Webex room API.
#######################################################################################
#TODO: Hard code webex chat room ID since we already know it
r = requests.get(
    f"{WEBEX_API_BASE}/rooms",
    headers={"Authorization": accessToken}
)

#######################################################################################
# DO NOT EDIT ANY BLOCKS WITH r.status_code (fixed formatting only)
#######################################################################################
if not r.status_code == 200:
    raise Exception(
        "Incorrect reply from Webex API. Status code: {}. Text: {}".format(
            r.status_code, r.text
        )
    )
#######################################################################################
# 4. Assign roomID to variable.
#######################################################################################

roomIdToGetMessages = "Y2lzY29zcGFyazovL3VybjpURUFNOnVzLXdlc3QtMl9yL1JPT00vYjZmZjM4NTAtY2IzNS0xMWYwLTkwNWYtZjk4MDg5M2EzNjgw"


######################################################################################
# WEBEX BOT CODE
#  Starts Webex bot to listen for and respond to /seconds messages.
######################################################################################

while True:
    time.sleep(1)
    GetParameters = {
        "roomId": roomIdToGetMessages, #TODO: replace this with hard coded roomID
        "max": 1
    }

    # 5. Provide the URL to the Webex messages API.
    r = requests.get(
        f"{WEBEX_API_BASE}/messages",
        params=GetParameters,
        headers={"Authorization": accessToken}
    )

    # verify if the returned HTTP status code is 200/OK
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
    message = messages[0]["text"]
    print("Received message: " + message)

    if message.find("/") == 0:
        if message[1:].isdigit():
            seconds = int(message[1:])
        else:
            raise Exception("Incorrect user input (must be /<number>).")

        # for the sake of testing, the max number of seconds is set to 5.
        if seconds > 5:
            seconds = 5

        time.sleep(seconds)

        # 6. Provide the URL to the ISS Current Location API.
        r = requests.get("http://api.open-notify.org/iss-now.json")

        json_data = r.json()

        if not json_data["message"] == "success":
            raise Exception(
                "Incorrect reply from Open Notify API. Status code: {}".format(
                    r.status_code
                )
            )

        # 7. Record the ISS GPS coordinates and timestamp.
        lat = json_data["iss_position"]["latitude"]
        lng = json_data["iss_position"]["longitude"]
        timestamp = json_data["timestamp"]

        # 8. Convert the timestamp epoch value to a human readable date and time.
        timeString = time.ctime(timestamp)

        # 9. Provide your Graphhopper API consumer key.
        key = "ddc44e53-27ac-445f-9c54-4a2f7c58e150"

        # 10. Provide the URL to the Graphhopper GeoCoding API.
        GeoURL = "https://graphhopper.com/api/1/geocode"

        # Use params so the query string is formed correctly
        params = {
            "key": key,
            "reverse": "true",
            "point": "{},{}".format(lat, lng)
        }
        r = requests.get(GeoURL, params=params)

        # Verify if the returned JSON data from the Graphhopper API service are OK
        json_data = r.json()
        if not r.status_code == 200:
            raise Exception("Graphhopper Error message: " + json_data.get("message", ""))

        # 11. Store the location received from the Graphhopper.
        hits = json_data.get("hits", [])
        if len(hits) != 0:
            hit = hits[0]
            CountryResult = hit.get("country", "Unknown")
            NameResult = hit.get("name", "Unknown Location")
            StateResult = hit.get("state", "")
            CityResult = hit.get("city", "")
            StreetResult = hit.get("street", "")
            HouseResult = hit.get("housenumber", "")
        else:
            CountryResult = "Unknown"
            NameResult = None

        # 12. Format the response message.
        # Example: On Tue Mar 12 00:16:04 2024 (GMT), the ISS was flying over Mobert Creek, Canada. (47.4917°, -37.3643°)
        if len(hits) == 0:
            responseMessage = (
                f"On {timeString} (GMT), the ISS was flying over a body of water or "
                f"unpopulated area at latitude {lat}° and longitude {lng}°."
            )
        else:
            responseMessage = (
                "On {} (GMT), the ISS was flying over {}, {}. ({:.4f}°, {:.4f}°)".format(
                    timeString,
                    NameResult,
                    CountryResult,
                    float(lat),
                    float(lng)
                )
            )

        # print the response message
        print("Sending to Webex: " + responseMessage)

        # 13. Post the message to the Webex room.
        HTTPHeaders = {
            "Authorization": accessToken,
            "Content-Type": "application/json"
        }

        PostData = {
            "roomId": roomIdToGetMessages,
            "text": responseMessage
        }

        # Post the call to the Webex message API.
        r = requests.post(
            f"{WEBEX_API_BASE}/messages",
            data=json.dumps(PostData),
            headers=HTTPHeaders
        )
        if not r.status_code == 200:
            raise Exception(
                "Incorrect reply from Webex API. Status code: {}. Text: {}".format(
                    r.status_code, r.text
                )
            )
