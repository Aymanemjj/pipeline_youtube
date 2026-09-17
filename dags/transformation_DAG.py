import os
import sys
from datetime import datetime
from airflow import DAG 
from airflow.operators.python import PythonOperator

sys.path.append("/opt/airflow")

from include import load
from include import transform

with DAG(
        dag_id="load_transform_data_DAG",
        start_date=datetime(2026, 9, 17),
        schedule=None,
        catchup=False
        ) as dag:


    make_staging_table = PythonOperator(
            task_id="make_staging_table",
            python_callable = load.create_staging_table
            )

    stage_data = PythonOperator(
            task_id="load_data_to_staging",
            python_callable=load.load_to_staging
            )
    
    get_staged_data = PythonOperator(
            task_id="load_staged_data",
            python_callable = load.load_from_staging
            )

    transform_data = PythonOperator(
            task_id="transform_staged_data",
            python_callable=transform.clean_data,
            op_kwargs={"data": get_staged_data.output}
            )

    calculate_basic_stats = PythonOperator(
            task_id="calculate_basic_stats",
            python_callable=transform.statistics,
            op_kwargs={"df": transform_data.output}
            )
    make_core_table = PythonOperator(
            task_id="make_core_id",
            python_callable=load.make_core_table
            )
    load_to_core = PythonOperator(
            task_id="load_data_to_core_table",
            python_callable=load.load_to_core,
            op_kwargs={"df": calculate_basic_stats.output}
            )






    make_staging_table >> stage_data >> get_staged_data >> transform_data >> calculate_basic_stats >> make_core_table >> load_to_core
