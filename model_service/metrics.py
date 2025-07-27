from prometheus_client import Counter, Gauge

anomaly_counter = Counter("anomalies_total", "Total anomalies", ["station_id"])
score_gauge = Gauge("anomaly_score", "Anomaly score", ["station_id"])
# Initialize metrics
for station in ["station_1", "station_2"]:
    anomaly_counter.labels(station_id=station).inc(0)