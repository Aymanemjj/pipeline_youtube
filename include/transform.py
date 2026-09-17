import pandas as pd
import re
import numpy as np

def clean_data(data):
    print(type(data))
    df = pd.DataFrame(data, columns=["videoId", "title", "publishedAt", "duration", "viewCount", "likeCount", "commentCount"])
    df.dropna(inplace=True)

    df["duration"] = df["duration"].apply(cleanDuration)
    df["publishedAt"] = pd.to_datetime(df["publishedAt"], format="mixed")

    df.dropna(inplace=True)

    df[["viewCount", "likeCount", "commentCount"]] = df[["viewCount", "likeCount", "commentCount"]].astype(int)

    return df


def cleanDuration(iso):
    RGX = r"^PT?(?:\d+Y)?(?:\d+M)?(?:\d+W)?(?:\d+D)?(?:T(?=\d)(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$"
    match = re.match(RGX, iso)
    if not match:
        return np.nan

    h = int(match.group(1) or "0")
    m = int(match.group(2) or "0")
    s = int(match.group(3) or "0")

    return h * 3600 + m * 60 + s


def statistics(df):
    view_count_safe = df["viewCount"].replace(0, np.nan)
    df["percentageOfLiking"] = ((df["likeCount"] / view_count_safe) * 100).round(2)
    df["percentageOfComenting"] = ((df["commentCount"] / view_count_safe) * 100).round(2)
    return df
