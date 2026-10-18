"""Order ETL pipeline (synthetic fixture modeled on Airflow DAG style)."""
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

default_args = {"owner": "data-eng", "retries": 1}

dag = DAG("orders_etl", schedule_interval="@daily", default_args=default_args)

extract_orders = PythonOperator(task_id="extract_orders", python_callable=lambda: None, dag=dag)
transform_orders = PythonOperator(task_id="transform_orders", python_callable=lambda: None, dag=dag)
audit_orders = BashOperator(task_id="audit_orders", bash_command="audit.sh", dag=dag)
load_orders = BashOperator(task_id="load_orders", bash_command="load.sh", dag=dag)

extract_orders >> [transform_orders, audit_orders] >> load_orders

# Nightly full-refresh window 02:00 UTC.
