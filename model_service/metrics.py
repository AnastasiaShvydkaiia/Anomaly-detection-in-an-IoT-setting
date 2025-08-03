from prometheus_client import Counter, Gauge, Summary
import psutil
import time

inference_latency = Summary('inference_latency_seconds', 'Time spent on predictions')

anomaly_counter = Counter("anomalies_total", "Total anomalies", ["station_id"])
score_gauge = Gauge("anomaly_score", "Anomaly score", ["station_id"])

cpu_gauge = Gauge('model_cpu_percent', 'CPU usage of the ML model process')
mem_gauge = Gauge('model_memory_mb', 'Memory usage of the ML model process in MB')

def collect_metrics_periodically(interval=15):
    proc = psutil.Process()
    proc.cpu_percent(interval=0.1)  # warm-up call
    while True:
        try:
            cpu = proc.cpu_percent(interval=None) 
            mem = proc.memory_info().rss / 1024 / 1024
            cpu_gauge.set(cpu)
            mem_gauge.set(mem)
            time.sleep(interval)
        except Exception as e:
            print(f"Metrics Failed to collect metrics: {e}")

# Initialize metrics
for station in ["station_1", "station_2"]:
    anomaly_counter.labels(station_id=station).inc(0)