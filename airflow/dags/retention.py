from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from sqlalchemy import create_engine, text

DATABASE_URL ="postgresql+psycopg2://postgres:mypassword@postgres:5432/mydb"
engine = create_engine(DATABASE_URL)

def delete_old_sensor_data():
    """Loads data and metadata for retraining"""
    query = text("""
            DELETE FROM predictions
            WHERE timestamp < NOW() - INTERVAL '30 days';
        """)
    with engine.connect() as conn:
        conn.execute(query)

with DAG(
    dag_id='sensor_data_retention',
    start_date=datetime(2025, 7, 1),
    schedule_interval='@daily',
    catchup=False
) as dag:

    delete_old_data = PythonOperator(
        task_id='delete_old_sensor_data',
        python_callable=delete_old_sensor_data,
    )
