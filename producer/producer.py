import time
import json
import numpy as np
from kafka import KafkaProducer
from datetime import datetime
import os

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC='sensor-data'

class Station:
    """Simulates sensor data"""
    def __init__(self,station_id):
        self.station_id=station_id
        # Initialize with the mean values
        self.base_temp =30 
        self.base_humidity = 20
        self.base_sound = 50

    def simulate(self):
        # Sample from the fitted distributions
        temp=np.random.beta(53.822, 46.706)*35+10 #10-45 degrees celcius
        humidity=np.random.beta(1.987, 7.945)*88 # 0-88%
        sound= np.random.beta(264.759, 261.590)*130-11 #-19-119 dB
        return {
            "station_id":self.station_id,
            "timestamp":datetime.utcnow().isoformat() + 'Z',
            "Temperature_Readings":round(temp,2),
            "Humidity_Levels":round(humidity,2),
            "Acoustic_Signals":round(sound,2)
        }

def stream_data(interval_seconds=15):
    """Continuously generates and sends data to the Kafka consumer"""
    stations=[Station(f"station_{i}") for i in range(1,3)]
    
    producer= KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

    while True:
        for station in stations:
            data=station.simulate()
            try:
                producer.send(TOPIC,key=station.station_id.encode('utf-8'),value=data)
                print("Produced:", data)
            except Exception as e:
                print(f"Failed to produce message: {data} → Error: {e}")

        time.sleep(interval_seconds)

if __name__ == "__main__":
    stream_data(interval_seconds=15)  # send every 15 seconds 

    