import mlflow
import mlflow.sklearn
import pandas as pd
import os
from sklearn.ensemble import IsolationForest
from sklearn.metrics import silhouette_score
from mlflow.models.signature import infer_signature
from mlflow.tracking import MlflowClient

class AnomalyDetector:
    def __init__(self, model_name="anomaly_model", stage="Production"):
        mlflow.set_tracking_uri("http://mlflow:5000")
        self.model_name = model_name
        self.stage = stage
        self.client = MlflowClient()
        self.model, self.version = self._load_model()

    def _load_model(self):
        try:
            model_uri = f"models:/{self.model_name}/{self.stage}"
            model = mlflow.sklearn.load_model(model_uri)

            # Get actual version
            versions = self.client.search_model_versions(f"name='{self.model_name}'")
            stage_version = next(
                (v for v in versions if v.current_stage == self.stage), None
            )
            version = stage_version.version if stage_version else None
            return model, version
        except Exception as e:
            raise RuntimeError("Model could not be loaded from MLflow Registry.") from e
            #return IsolationForest( contamination=0.001, random_state=42), None

    def train(self, X: pd.DataFrame, metadata: dict = {}):
        mlflow.set_experiment("Anomaly_Detection")
        with mlflow.start_run(run_name='training') as run:
            self.model.fit(X)
            labels = self.model.predict(X)
            score = silhouette_score(X, labels)

            mlflow.log_params(self.model.get_params())
            mlflow.log_params(metadata)
            mlflow.log_metric("silhouette_score", score)
            mlflow.log_metric('mean_score', self.model.decision_function(X).mean())

            # Save a snapshot of training data
            train_data_path = "training_data.csv"
            X.to_csv(train_data_path, index=False)
            mlflow.log_artifact(train_data_path, artifact_path='training_data')
            os.remove(train_data_path)

            # Register the model
            result = mlflow.sklearn.log_model(
                sk_model=self.model,
                registered_model_name=self.model_name,
                input_example=X.iloc[:1],
                signature=infer_signature(X, self.model.predict(X))
            )

            # Promote to Production stage
            new_version = self.client.get_latest_versions(self.model_name)[-1].version
            self.client.transition_model_version_stage(
                name=self.model_name,
                version=new_version,
                stage="Production",
                archive_existing_versions=True
            )

            # Reload model and update internal version
            self.model, self.version = self._load_model()

    def get_model_parameters(self, filename: str = "training_data.csv"):
        """Return params & training data snapshot for this model version."""
        mv = self.client.get_model_version(self.model_name, self.version)
        run = self.client.get_run(mv.run_id)
        artifact_uri = f"runs:/{mv.run_id}/training_data/{filename}"
        local_path = mlflow.artifacts.download_artifacts(artifact_uri)
        df = pd.read_csv(local_path)
        return run.data.params, df

    def predict(self, X: pd.DataFrame):
        return self.model.predict(X)

    def predict_score(self, X: pd.DataFrame):
        return self.model.decision_function(X)
