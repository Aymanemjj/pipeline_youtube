import os
import pprint as pr
import json
from textwrap import indent

import requests as rqst
from dotenv import load_dotenv

# Loading .env variables
load_dotenv(dotenv_path="../.env")
BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")
CHANNEL_HANDLE = os.getenv("CHANNEL_HANDLE")



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

get_video_details = {
    "key" : API_KEY,
    "part" : "contentDetails,statistics",
    "id":None
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


def getVidDetails(json):
    L = []
    for i in json:
        L.append(i["contentDetails"]["videoId"])
    ids = ",".join(L)
    get_video_details["id"]=ids
    r = rqst.get(BASE_URL + "/videos",get_video_details)
    # pr.pprint(r.status_code)
    return r.json()["items"]

    
def loadVidIdToJson(list):
    for i in list:
        del i["etag"], i["contentDetails"]["caption"], i["contentDetails"]["contentRating"], i["statistics"]["favoriteCount"]
    json.dump(list, VID_DATA_FILE, ensure_ascii=False, indent=4)

        
PLAYLIST_ID = getCreatorPlaylist(get_creator_playlist)


#Temp .txt file for video IDs
with open("../data/vid_data.json","w", encoding='utf-8') as VID_DATA_FILE:
    while True:
        response = getPlaylistDetails(PLAYLIST_ID, get_playlist_details)
        # pr.pprint(response["items"])
        items = getVidDetails(response['items'])
        loadVidIdToJson(items)
        # pr.pprint(response)
        if "nextPageToken" not in response:
            break
        else:
            get_playlist_details["pageToken"] = response["nextPageToken"]


