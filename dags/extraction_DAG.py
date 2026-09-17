import os
import sys
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
sys.path.append("/opt/airflow")

from include import extract as extract_data




with DAG(
        dag_id="extraction_DAG",
        start_date=datetime(2026, 9, 17),
        schedule="@hourly",
        catchup=False
        ) as dag:


    get_creator_playlist = PythonOperator(
            task_id = "get_creator_playlist",
            python_callable = extract_data.getCreatorPlaylist,
            )
    get_video_details = PythonOperator(
            task_id = "get_playlist_details_and_videos",
            python_callable = extract_data.getPlaylistDetails,
            op_kwargs = {"playlist_id": get_creator_playlist.output}
            )
    save_to_json = PythonOperator(
            task_id = "save_data_to_json",
            python_callable = extract_data.save_to_json,
            op_kwargs = {"BUFFER" : get_video_details.output}
            )

    
    trigger_load = TriggerDagRunOperator(
            task_id="trigger_load_dag",
            trigger_dag_id="load_transform_data_DAG",
            )
    get_creator_playlist >> get_video_details >> save_to_json >> trigger_load
