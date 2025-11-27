######################################################################################
# This program:
# - Asks the user to enter an access token or use the hard coded access token.
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
# 2. Ask the user for the Webex access token, or use hard-coded token.
#######################################################################################

# Hard-coded token (REPLACE with your token if you want to use it)
hard_coded_token = "ZjAzMGVlNGItMjVmZi00MGI2LTk3NDYtYjViMTllNzA2ZmQ3ZjRiODk5NjAtZTM1_P0A1_e58072af-9d57-4b13-abf7-eb3b506c964d"

choice = input("Do you wish to use the hard-coded Webex token? (y/n) ")

if choice == "n" or choice == "N":
    accessToken = input("What is your access token? ").strip()
else:
    if not hard_coded_token:
        raise RuntimeError("No hard-coded token set. Edit the script or choose 'n' to enter a token.")
    accessToken = hard_coded_token

accessToken = "Bearer " + accessToken

#######################################################################################
# 3. Provide the URL to the Webex room API.
#######################################################################################

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
# 4. Create a loop to print the type and title of each room.
#######################################################################################

print("\nList of available rooms:")
rooms = r.json()["items"]
for room in rooms:
    print("Type: '{}' Name: {}".format(room["type"], room["title"]))

#######################################################################################
# SEARCH FOR WEBEX ROOM TO MONITOR
# DO NOT EDIT CODE IN THIS BLOCK
#######################################################################################

while True:
    roomNameToSearch = input("Which room should be monitored for the /seconds messages? ")
    roomIdToGetMessages = None

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

######################################################################################
# WEBEX BOT CODE
#  Starts Webex bot to listen for and respond to /seconds messages.
######################################################################################

while True:
    time.sleep(1)
    GetParameters = {
        "roomId": roomIdToGetMessages,
        "max": 1
    }

    # 5. Provide the URL to the Webex messages API.
    r = requests.get(
        f"{WEBEX_API_BASE}/messages",
        params=GetParameters,
        headers={"Authorization": accessToken}
    )

    # verify if the retuned HTTP status code is 200/OK
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
