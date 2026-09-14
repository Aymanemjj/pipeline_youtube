import os
import pprint as pr

import requests as rqst
from dotenv import load_dotenv

# Loading .env variables
load_dotenv(dotenv_path="../.env")
BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")
CHANNEL_HANDLE = os.getenv("CHANNEL_HANDLE")

#Temp JSON file for video IDs
VID_ID_JSON = open("../data/vid_id.txt","w")


# Params for each request
get_creator_playlist = {
    "key" : API_KEY,
    "forHandle" : CHANNEL_HANDLE,
    "part" : "contentDetails"
}

get_playlist_details = {
    "key": API_KEY,
    "part": "contentDetails",
    "playlistId": None,
    "maxResults": 50,
}




def getCreatorPlaylist(params):
    r = rqst.get(BASE_URL + "/channels", params)
    data = r.json()
    uploads_playlist_id = data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    return uploads_playlist_id

def getPlaylistDetails(playlist_id, params):
    params["playlistId"] = playlist_id
    # print(params)
    r = rqst.get(BASE_URL + "/playlistItems", params)
    return r.json()

def loadVidIdToJson(json):
    for i in json:
        VID_ID_JSON.write(f"{i["contentDetails"]["videoId"]}\n")
    

PLAYLIST_ID = getCreatorPlaylist(get_creator_playlist)



while True:
    response = getPlaylistDetails(PLAYLIST_ID, get_playlist_details)
    
    loadVidIdToJson(response["items"])
    # pr.pprint(response)
    if "nextPageToken" not in response:
        break
    else:
        get_playlist_details["pageToken"] = response["nextPageToken"]


    
VID_ID_JSON.close()