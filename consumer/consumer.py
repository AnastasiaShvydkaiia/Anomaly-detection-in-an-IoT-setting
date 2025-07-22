from kafka import KafkaConsumer
import requests
import json
import os

API_URL = os.getenv("API_URL", "http://api:8000/predict")
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC='sensor-data'

consumer=KafkaConsumer(
    TOPIC, 
    bootstrap_servers=BOOTSTRAP_SERVERS, 
    group_id='consumer-group',
    value_deserializer=lambda m:json.loads(m.decode('utf-8')),
    key_deserializer=lambda k:k.decode('utf-8') if k else None,
    auto_offset_reset='earliest'
)

for message in consumer:
    data=message.value
    try:
        response=requests.post(API_URL, json=data)
        prediction=response.json()
        print("Received JSON:", data)
        print('API Response:', prediction)
    except Exception as e:
        print("Error: ",e)