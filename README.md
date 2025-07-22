# Anomaly detection in an IoT setting (stream processing)
## About
This project implements an end-to-end pipeline for real-time anomaly detection in sensor data using:

- **Flask** – REST API server for predictions and drift detection
- **Kafka** – streaming simulation of sensor stations
- **Scikit-learn** – model training with Isolation Forest
- **MLflow** – model tracking and versioning
- **Prometheus + Grafana** – monitoring and metrics visualization
- **Docker + Docker Compose** – containerized deployment

##  Prerequisites

- Docker & Docker Compose

## Usage

1. **Clone the repo:**

```git clone https://github.com/yourname/anomaly-detection.git```

```cd anomaly-detection```

2. **Start the system:**

```docker-compose up --build```

3. **Access:**

- API: http://localhost:8000

- Prometheus: http://localhost:9090

- Grafana: http://localhost:3000 (admin/admin)

- MLflow UI: http://localhost:5000