import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
import os

mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"))

MODEL_NAME = "anomaly_model"

class ModelLoader:
    def __init__(self):
        self.model = None
        self.load_latest_model()

    def load_latest_model(self):
        print("Loading latest model from MLflow...")
        client = MlflowClient()
        self.model = mlflow.sklearn.load_model(f"models:/{MODEL_NAME}/Production")
         # Get actual version
        versions = client.search_model_versions(f"name='{MODEL_NAME}'")
        stage_version = next((v for v in versions if v.current_stage == "Production"), None)
        version = stage_version.version if stage_version else None
        print(f"Model {MODEL_NAME} (ver. {version}) loaded.")

    def get_model(self):
        return self.model
