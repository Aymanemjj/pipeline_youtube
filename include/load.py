import os
import pprint as pr

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values

# Loading .env variables
load_dotenv(dotenv_path="../.env")
conn = psycopg2.connect(
    dbname="youtube_elt",
    user=os.getenv("POSTGRES_CONN_USERNAME"),
    password=os.getenv("POSTGRES_CONN_PASSWORD"),
    host=os.getenv("POSTGRES_CONN_HOST"),
    port=os.getenv("POSTGRES_CONN_PORT"),
)

cur = conn.cursor()


def create_staging_table():
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS videos_staging (
            "videoId" TEXT PRIMARY KEY ,
            "title" TEXT,
            "publishedAt" TEXT,
            "duration" TEXT,
            "viewCount" TEXT,
            "likeCount" TEXT,
            "commentCount" TEXT
        );

        """
    )

    conn.commit()


def load_to_staging():
    df = pd.read_json("data/vid_data.json")
    records = df.values.tolist()

    execute_values(
        cur,
        """
        INSERT INTO videos_staging ("videoId", "title", "publishedAt", "duration", "viewCount", "likeCount", "commentCount")
        VALUES %s
        ON CONFLICT ("videoId")
        DO UPDATE SET
            "title" = EXCLUDED."title",
            "publishedAt" = EXCLUDED."publishedAt",
            "duration" = EXCLUDED."duration",
            "viewCount" = EXCLUDED."viewCount",
            "likeCount" = EXCLUDED."likeCount",
            "commentCount" = EXCLUDED."commentCount"
        """,
        records,
    )
    conn.commit()


def load_from_staging():
    cur.execute(
        """
            SELECT * FROM videos_staging
            """
    )
    rows = cur.fetchall()
    return rows


def make_core_table():
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS videos_core (
                "videoId" TEXT PRIMARY KEY ,
                "title" TEXT,
                "publishedAt" TIMESTAMP NOT NULL,
                "duration" BIGINT NOT NULL,
                "viewCount" BIGINT NOT NULL,
                "likeCount" BIGINT NOT NULL,
                "commentCount" BIGINT NOT NULL,
                "percentageOfLiking" INT NOT NULL,
                "percentageOfComenting" INT NOT NULL
            );
        """
    )

    conn.commit()


def load_to_core(df):
    if df.empty:
        return
    records = df.values.tolist()
    ids = df["videoId"].tolist()
    execute_values(
        cur,
        """
        INSERT INTO videos_core ("videoId", "title", "publishedAt", "duration", "viewCount", "likeCount", "commentCount", "percentageOfLiking", "percentageOfComenting")
        VALUES %s
        ON CONFLICT ("videoId")
        DO UPDATE SET
            "title" = EXCLUDED."title",
            "publishedAt" = EXCLUDED."publishedAt",
            "duration" = EXCLUDED."duration",
            "viewCount" = EXCLUDED."viewCount",
            "likeCount" = EXCLUDED."likeCount",
            "commentCount" = EXCLUDED."commentCount",
            "percentageOfLiking" = EXCLUDED."percentageOfLiking",
            "percentageOfComenting" = EXCLUDED."percentageOfComenting"
        """,
        records,
    )


    cur.execute(
        """DELETE FROM videos_core WHERE "videoId" != ALL(%s)""",
        (ids,)
    )

    conn.commit()
