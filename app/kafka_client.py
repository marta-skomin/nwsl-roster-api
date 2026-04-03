import json
from kafka import KafkaProducer
import os
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
_producer = None

def get_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers='localhost:9092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8'),
        )
    return _producer

def publish_player_event(event_type: str, player: dict):
    """Publish a player event to Kafka."""
    try:
        producer = get_producer()
        producer.send(
            topic='nwsl-players',
            key=event_type,
            value=player,
        )
        producer.flush()
        print(f"Published {event_type} event for {player['name']}")
    except Exception as e:
        # don't crash the API if Kafka is unavailable
        print(f"Kafka unavailable, skipping event publish: {e}")
