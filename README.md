# Anomaly detection in an IoT setting (stream processing)
## About
This project implements an end-to-end pipeline for real-time anomaly detection in sensor data using:

- **Flask** – REST API server for predictions and drift detection
- **Kafka** – streaming simulation of sensor stations
- **Scikit-learn** – model training with Isolation Forest
- **MLflow** – model tracking and versioning
- **Prometheus + Grafana** – monitoring and metrics visualization
- **Docker + Docker Compose** – containerized deployment

## Architecture

**Frontend**\
The application has a web interface served via Flask using simple HTML templates, primarily for triggering model actions such as retraining or drift checks.

**Backend API**\
A Python Flask API acts as the main service, exposing endpoints for anomaly detection, health checks, and model drift checks. It connects to a PostgreSQL database for data persistence, consumes data from Kafka topics, and integrates with MLflow for model tracking and versioning. The API also exposes application and model metrics to Prometheus.

**Model Inference & Monitoring**\
The Flask service performs inference using a deployed ML model. It tracks predictions, anomaly scores, and metrics like active anomalies using Prometheus. These metrics are visualized in Grafana and can be used for alerting or monitoring model health over time.

**Asynchronous Messaging**\
Kafka is used as a message broker for asynchronous data ingestion, enabling decoupling between data producers and the anomaly detection pipeline. 

**Model Lifecycle & Tracking**\
MLflow is used to log and manage trained models, allowing reproducibility, versioning, and easy reloading in production via the MLFLOW_TRACKING_URI.

**Database**\
PostgreSQL is used to persist configuration, metadata, or raw data related to the models or predictions. It is initialized via an SQL script during Docker container startup. 

**Prometheus & Grafana**\
Prometheus scrapes metrics from the Flask service (via a /metrics endpoint) and stores time-series data. Grafana connects to Prometheus as a datasource and visualizes model health, anomaly counts, and request performance. Custom metrics include request latency, prediction counts, anomaly frequency, and more.

While we could have split the system into separate microservices—for example, having a dedicated model service, drift detection service, or separate data ingest pipeline—we chose to keep the system simple and maintainable by using a unified backend.

##  Prerequisites

- Docker & Docker Compose

## Usage

1. **Clone the repo:**

```git clone https://github.com/AnastasiaShvydkaiia/Anomaly-detection-in-an-IoT-setting.git```

```cd anomaly-detection```

2. **Start the system:**

```docker-compose up --build```

3. **Access:**

- API: http://localhost:8000

- Prometheus: http://localhost:9090

- Grafana: http://localhost:3000 (admin/admin)

- MLflow UI: http://localhost:5000

## Conclusion

The project successfully demonstrated a scalable anomaly detection system trained on real industrial sensor data (from Kaggle), integrated into a simulated factory streaming environment. The system is portable, easily monitorable, and ready for adaptation to real-time industrial applications once live data is available