from prometheus_client import Summary, Gauge, Counter, generate_latest

anomaly_counter = Counter("anomalies_detected_total", "Detected anomalies",['station_id'])
score_gauge = Gauge("last_anomaly_score", "Last anomaly score",['station_id'])
request_latency=Summary('http_request_duration_seconds','Time spent handling requests')


def get_metrics():
    return generate_latest()