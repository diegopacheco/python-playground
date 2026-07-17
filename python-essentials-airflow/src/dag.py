from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator


def extract(**context):
    numbers = [1, 2, 3, 4, 5]
    context["ti"].xcom_push(key="numbers", value=numbers)


def transform(**context):
    numbers = context["ti"].xcom_pull(key="numbers", task_ids="extract")
    squares = [n * n for n in numbers]
    context["ti"].xcom_push(key="squares", value=squares)


def load(**context):
    squares = context["ti"].xcom_pull(key="squares", task_ids="transform")
    print(f"loaded squares: {squares} total={sum(squares)}")


with DAG(
    dag_id="python_essentials_etl",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["essentials"],
) as dag:
    extract_task = PythonOperator(task_id="extract", python_callable=extract)
    transform_task = PythonOperator(task_id="transform", python_callable=transform)
    load_task = PythonOperator(task_id="load", python_callable=load)

    extract_task >> transform_task >> load_task
