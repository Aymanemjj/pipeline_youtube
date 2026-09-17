import os
import pprint as pr
import json

from textwrap import indent

import pandas as pd

import requests as rqst
from dotenv import load_dotenv

from datetime import datetime


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
    "part" : "contentDetails,statistics,snippet",
    "id":None
}



def getCreatorPlaylist():
    r = rqst.get(BASE_URL + "/channels", get_creator_playlist)
    data = r.json()
    uploads_playlist_id = data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    return uploads_playlist_id

def getPlaylistDetails(playlist_id):
    BUFFER = []
    get_playlist_details["playlistId"] = playlist_id
    while True:
        r = rqst.get(BASE_URL + "/playlistItems",get_playlist_details)
        response = r.json()
        detailsList = response["items"]

        BUFFER.extend(getVidDetails(detailsList))

        if "nextPageToken" not in response:
            break
        else:
            get_playlist_details["pageToken"] = response["nextPageToken"]
    return BUFFER


def getVidDetails(detailsList):
    L = []

    for i in detailsList:
        L.append(i["contentDetails"]["videoId"])
    ids = ",".join(L)
    get_video_details["id"]=ids
    r = rqst.get(BASE_URL + "/videos",get_video_details)
    # pr.pprint(r.status_code)
    return r.json()["items"]


def loadVidIdToJson(list):
    to_save = []
    for i in list:
        to_save.append({
            "videoId": i["id"],
            "title":i["snippet"]["title"],
            "publishedAt":i["snippet"]["publishedAt"],
            "duration":i["contentDetails"]["duration"],
            "viewCount":i["statistics"]["viewCount"],
            "likeCount":i["statistics"]["likeCount"],
            "commentCount":i["statistics"]["commentCount"]
        })
    return to_save





def save_to_json(BUFFER):
        to_save = loadVidIdToJson(BUFFER)
        with open(f"data/{datetime.now()}.json","w", encoding='utf-8') as VID_DATA_FILE:
            json.dump(to_save, VID_DATA_FILE, ensure_ascii=False, indent=4)
