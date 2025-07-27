from kafka import KafkaConsumer
import json
from predict import handle_prediction
from model_loader import ModelLoader
import os

bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

loader = ModelLoader()

def listen_to_sensor_data():
    try:
        consumer = KafkaConsumer(
            'sensor-data',
            bootstrap_servers=bootstrap_servers,
            group_id="model-service",
            value_deserializer=lambda m:json.loads(m.decode('utf-8')),
            key_deserializer=lambda k:k.decode('utf-8') if k else None,
            auto_offset_reset='earliest',
            enable_auto_commit=False
        )
        for message in consumer:
            print(f"Received message: {message.value}")
            handle_prediction(message.value, loader.get_model())
    except Exception as e:
        print(f"Sensor Consumer Error: {e}")

def listen_to_model_update():
    try:
        consumer = KafkaConsumer(
            "model-update",
            bootstrap_servers='kafka:9092',
            group_id="model-service-reload",
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        for message in consumer:
            print(" Model update message received.")
            loader.load_latest_model()
    except Exception as e:
        print(f"Model update consumer Error: {e}")


