from prometheus_client import Summary, Gauge, Counter, generate_latest

#PROMETHEUS_PORT=int(os.environ.get("PROMETHEUS_PORT",9090))

prediction_counter = Gauge("predictions_total", "Total number of predictions",['station_id'])
anomaly_counter = Counter("anomalies_detected_total", "Detected anomalies",['station_id'])
score_gauge = Gauge("last_anomaly_score", "Last anomaly score",['station_id'])
request_latency=Summary('http_request_duration_seconds','Time spent handling requests')
active_anomalies = Gauge("active_anomalies", "Current number of active anomalies",['station_id'])

def get_metrics():
    return generate_latest()