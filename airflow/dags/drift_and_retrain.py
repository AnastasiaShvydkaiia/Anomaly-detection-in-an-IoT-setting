
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from datetime import datetime, timedelta
from scipy.stats import ks_2samp
from sqlalchemy import create_engine, text
import pandas as pd
import mlflow
from mlflow.tracking import MlflowClient
import mlflow.sklearn
import os
from sklearn.ensemble import IsolationForest
from sklearn.metrics import silhouette_score
from mlflow.models.signature import infer_signature
from kafka import KafkaProducer
import json
import hashlib

mlflow.set_tracking_uri("http://mlflow:5000")
mlflow.set_experiment("Anomaly_Detection")
client = MlflowClient()
model = IsolationForest(contamination=0.01, random_state=42)
DATABASE_URL ="postgresql+psycopg2://postgres:mypassword@postgres:5432/mydb"
engine = create_engine(DATABASE_URL)

def load_production_data(days=7):
    """Loads data and metadata for retraining"""
    query = text(f"""
        SELECT id, temperature as "Temperature_Readings", 
               humidity as "Humidity_Levels", 
               sound_volume as "Acoustic_Signals"
        FROM predictions
        WHERE timestamp > now() - interval '{days} days'
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
        metadata = {
            "row_count": len(df),
            "row_id_min": df["id"].min(),
            "row_id_max": df["id"].max(),
            "data_hash": hashlib.sha256(pd.util.hash_pandas_object(df, index=True).values.tobytes()).hexdigest()
        }
    return df.drop(columns=["id"]), metadata

def load_reference_data(model_name="anomaly_model", stage="Production",filename= "training_data.csv"):
    """Return training data snapshot for this model version."""
    versions = client.search_model_versions(f"name='{model_name}'")
    stage_version = next((v for v in versions if v.current_stage == stage), None)
    version = stage_version.version if stage_version else None
    
    mv = client.get_model_version(model_name, version)
    artifact_uri = f"runs:/{mv.run_id}/training_data/{filename}"
    local_path = mlflow.artifacts.download_artifacts(artifact_uri)
    df = pd.read_csv(local_path)
    return df

def retrain_model(model_name="anomaly_model", metadata={}):
    with mlflow.start_run(run_name='training') as run:
        X,metadata=load_production_data()
        model.fit(X)
        labels = model.predict(X)
        score = silhouette_score(X, labels)

        mlflow.log_params(model.get_params())
        mlflow.log_params(metadata)
        mlflow.log_metric("silhouette_score", score)
        mlflow.log_metric('mean_score', model.decision_function(X).mean())

        # Save a snapshot of training data
        train_data_path = "training_data.csv"
        X.to_csv(train_data_path, index=False)
        mlflow.log_artifact(train_data_path, artifact_path='training_data')
        os.remove(train_data_path)

        # Register the model
        mlflow.sklearn.log_model(
            sk_model=model,
            registered_model_name=model_name,
            input_example=X.iloc[:1],
            signature=infer_signature(X, model.predict(X))
        )

        # Promote to Production stage
        new_version = client.get_latest_versions(model_name)[-1].version
        client.transition_model_version_stage(
            name=model_name,
            version=new_version,
            stage="Production",
            archive_existing_versions=True
        )

def check_ks_drift(ref_df, prod_df):
    drift_results = {}
    drift_detected = False
    for column in ref_df.columns:
        stat, p_value = ks_2samp(ref_df[column], prod_df[column])
        drift_results[column] = {'p_value': p_value}
        if p_value < 0.05:
            drift_detected = True
    return drift_detected, drift_results

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

def notify_model_update():
    producer = KafkaProducer(
        bootstrap_servers='kafka:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    message = {
        "event": "model_updated",
        "model_name": "anomaly_model",
        "stage": "Production"
    }
    producer.send("model-update", value=message)
    producer.flush()

def run_drift_check(**context):
    ref = load_reference_data()
    prod = load_production_data()
    if len(prod) < 1000:                          # for testing
        context['ti'].xcom_push(key='drift_detected', value=False)
        return "skip_retraining"
    drift, _ = check_ks_drift(ref, prod)
    context['ti'].xcom_push(key='drift_detected', value=drift)
    return "retrain_model" if drift else "skip_retraining"

def skip():
    print("No drift detected — skipping retrain")

with DAG(
    dag_id="drift_and_retrain",
    start_date=datetime(2023, 1, 1),
    schedule_interval="*/5 * * * *",
    catchup=False
) as dag:

    detect_drift = BranchPythonOperator(
        task_id="check_drift",
        python_callable=run_drift_check,
        provide_context=True,
    )

    retrain = PythonOperator(
        task_id="retrain_model",
        python_callable=retrain_model,
    )

    skip_retrain = PythonOperator(
        task_id="skip_retraining",
        python_callable=skip,
    )

    detect_drift >> [retrain, skip_retrain]

    notify_update = PythonOperator(
    task_id='notify_model_service',
    python_callable=notify_model_update,
    )
    retrain >> notify_update
