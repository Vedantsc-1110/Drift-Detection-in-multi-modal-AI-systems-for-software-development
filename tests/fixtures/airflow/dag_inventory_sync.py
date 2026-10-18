"""Hourly inventory sync (synthetic fixture)."""
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

with DAG("inventory_sync", schedule="@hourly", default_args={"owner": "fulfillment"}) as dag:
    check_stock = PythonOperator(task_id="check_stock", python_callable=lambda: None)
    reorder = BashOperator(task_id="reorder", bash_command="reorder.sh")

    reorder << check_stock

# Reorder point evaluated per warehouse.
